from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Header, Form, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import csv
import io
import json
import threading
import uuid
from app.schemas.schemas import (
    CreateTableRequest, TableInfo, ImportResponse,
    ImportHistoryResponse, RowCreateRequest, RowUpdateRequest, RowsDeleteRequest,
    TableVersionResponse, RollbackResponse
)
from app.models import get_db, ImportHistory, TableSchema, User, TablePermission, SessionLocal, TableVersion
from app.utils.db_manager import (
    create_table, drop_table, get_table_info, get_all_tables, insert_rows,
    get_row_count, get_table_data, create_row, update_row, delete_rows,
    get_table_snapshot, restore_table_snapshot
)
from app.utils.csv_handler import parse_csv, preview_csv, decode_csv_bytes, validate_csv_against_table_schema
from app.routes.auth import get_current_user
from app.utils.permissions import (
    get_user_by_username,
    is_admin,
    has_table_permission,
    ensure_owner_permissions,
    require_table_permission,
)
from app.utils.audit import log_audit_event
from app.utils.connection_manager import resolve_data_session

router = APIRouter(prefix="/api/tables", tags=["Tables"])
import_jobs: Dict[str, Dict[str, Any]] = {}
import_jobs_lock = threading.Lock()


def _set_import_job_state(job_id: str, **fields: Any) -> None:
    with import_jobs_lock:
        existing = import_jobs.get(job_id, {})
        existing.update(fields)
        import_jobs[job_id] = existing


def _create_table_version_snapshot(
    meta_db: Session,
    data_db: Session,
    user_id: int,
    table_name: str,
    action: str,
    message: Optional[str] = None,
) -> TableVersion:
    snapshot_rows = get_table_snapshot(data_db, table_name)
    version = TableVersion(
        user_id=user_id,
        table_name=table_name,
        action=action,
        version_data={
            "rows": snapshot_rows,
            "row_count": len(snapshot_rows),
            "message": message,
        },
    )
    meta_db.add(version)
    return version


def _parse_import_request(
    table_name: Optional[str],
    request: Optional[str],
) -> tuple[str, Dict[str, str], Optional[str], str, Optional[List[Dict[str, Any]]]]:
    request_table_name = table_name
    columns_mapping: Dict[str, str] = {}
    delimiter: Optional[str] = None
    encoding: str = "utf-8"
    edited_preview_rows: Optional[List[Dict[str, Any]]] = None

    if request:
        try:
            request_payload: Any = request

            for _ in range(2):
                if isinstance(request_payload, str):
                    normalized_payload = request_payload.replace('\\"', '"')
                    parsed_payload = json.loads(normalized_payload)
                    if isinstance(parsed_payload, str):
                        request_payload = parsed_payload
                        continue
                    request_payload = parsed_payload
                    break

            if not isinstance(request_payload, dict):
                raise ValueError("Invalid JSON in request field")

            request_table_name = request_payload.get("table_name", request_table_name)
            request_mapping = request_payload.get("columns_mapping")
            if isinstance(request_mapping, dict) and request_mapping:
                columns_mapping = request_mapping
            request_delimiter = request_payload.get("delimiter")
            if isinstance(request_delimiter, str) and request_delimiter in [",", ";", "\t"]:
                delimiter = request_delimiter
            request_encoding = request_payload.get("encoding")
            if isinstance(request_encoding, str) and request_encoding:
                encoding = request_encoding
            request_edited_rows = request_payload.get("edited_preview_rows")
            if isinstance(request_edited_rows, list):
                edited_preview_rows = request_edited_rows
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON in request field")

    if not request_table_name:
        raise ValueError("table_name is required")

    return request_table_name, columns_mapping, delimiter, encoding, edited_preview_rows


def _execute_import(
    meta_db: Session,
    data_db: Session,
    user_id: int,
    file_name: str,
    content: bytes,
    request_table_name: str,
    columns_mapping: Dict[str, str],
    delimiter: Optional[str],
    encoding: str,
    edited_preview_rows: Optional[List[Dict[str, Any]]],
    progress_callback: Optional[Any] = None,
) -> ImportResponse:
    if progress_callback:
        progress_callback(10, "Подготовка данных")

    file_content = decode_csv_bytes(content, encoding=encoding)

    if progress_callback:
        progress_callback(30, "Парсинг CSV")

    headers, rows = parse_csv(file_content, delimiter=delimiter)

    if not columns_mapping:
        columns_mapping = {header: header for header in headers}

    if edited_preview_rows is not None:
        rows = edited_preview_rows

    if not rows:
        raise ValueError("CSV file is empty")

    table_info = get_table_info(data_db, request_table_name)
    columns_config = {col.name: col.type for col in table_info.columns}

    if not all(csv_col in headers for csv_col in columns_mapping.keys()):
        raise ValueError("Mapping contains CSV columns that are not present in file")

    if not all(db_col in columns_config for db_col in columns_mapping.values()):
        raise ValueError("Mapping contains table columns that do not exist")

    _create_table_version_snapshot(
        meta_db=meta_db,
        data_db=data_db,
        user_id=user_id,
        table_name=request_table_name,
        action="import_before",
        message=f"Before CSV import: {file_name}",
    )

    if progress_callback:
        progress_callback(60, "Валидация строк")

    valid_rows, errors = validate_csv_against_table_schema(
        rows,
        columns_config,
        columns_mapping
    )

    inserted_count = 0
    if valid_rows:
        if progress_callback:
            progress_callback(85, "Запись в базу данных")
        inserted_count = insert_rows(data_db, request_table_name, valid_rows)

    history = ImportHistory(
        user_id=user_id,
        table_name=request_table_name,
        file_name=file_name,
        rows_imported=inserted_count,
        status="success" if not errors else "partial",
        validation_errors=[{"row": e.row, "error": e.error} for e in errors]
    )
    meta_db.add(history)
    meta_db.commit()

    if progress_callback:
        progress_callback(100, "Импорт завершён")

    return ImportResponse(
        success=len(errors) == 0,
        rows_imported=inserted_count,
        errors=errors,
        warnings=[] if len(errors) == 0 else [f"Found {len(errors)} validation errors"],
        message=f"Successfully imported {inserted_count} rows" if inserted_count > 0 else "No rows imported"
    )


def _run_import_job(
    job_id: str,
    user_id: int,
    file_name: str,
    content: bytes,
    request_table_name: str,
    columns_mapping: Dict[str, str],
    delimiter: Optional[str],
    encoding: str,
    edited_preview_rows: Optional[List[Dict[str, Any]]],
) -> None:
    meta_db = SessionLocal()
    data_db = None
    close_data_db = False
    try:
        _set_import_job_state(job_id, status="running", progress=5, message="Запуск задачи")

        user = meta_db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found for import job")

        data_db, close_data_db, _ = resolve_data_session(meta_db, user)

        def progress(progress_value: int, message: str) -> None:
            _set_import_job_state(job_id, status="running", progress=progress_value, message=message)

        result = _execute_import(
            meta_db=meta_db,
            data_db=data_db,
            user_id=user_id,
            file_name=file_name,
            content=content,
            request_table_name=request_table_name,
            columns_mapping=columns_mapping,
            delimiter=delimiter,
            encoding=encoding,
            edited_preview_rows=edited_preview_rows,
            progress_callback=progress,
        )

        _set_import_job_state(
            job_id,
            status="completed",
            progress=100,
            message="Импорт завершён",
            result={
                "success": result.success,
                "rows_imported": result.rows_imported,
                "errors": [e.model_dump() for e in result.errors],
                "warnings": result.warnings,
                "message": result.message,
            },
        )
        if user:
            log_audit_event(
                meta_db,
                user,
                action="table_import_async_completed",
                entity_type="table",
                entity_name=request_table_name,
                details={"rows_imported": result.rows_imported, "file_name": file_name},
            )
            meta_db.commit()
    except Exception as e:
        meta_db.rollback()
        _set_import_job_state(job_id, status="failed", message=str(e))
        user = meta_db.query(User).filter(User.id == user_id).first()
        if user:
            log_audit_event(
                meta_db,
                user,
                action="table_import_async_failed",
                entity_type="table",
                entity_name=request_table_name,
                status="failed",
                details={"error": str(e), "file_name": file_name},
            )
            meta_db.commit()
    finally:
        if close_data_db and data_db is not None:
            data_db.close()
        meta_db.close()


def get_user_from_header(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """Resolve authenticated user from Authorization header"""
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    try:
        token = authorization.replace("Bearer ", "")
        username = get_current_user(token)
        user = get_user_by_username(db, username)
        return user
    except HTTPException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


@router.post("/create", response_model=TableInfo)
async def create_new_table(
    request: CreateTableRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_from_header)
):
    """Create a new table in the database"""
    data_db, close_data_db, connection_name = resolve_data_session(db, current_user)
    try:
        create_table(data_db, request.table_name, request.columns)

        schema = TableSchema(
            user_id=current_user.id,
            table_name=request.table_name,
            columns_config=[column.model_dump() for column in request.columns],
        )
        db.add(schema)
        ensure_owner_permissions(db, current_user, request.table_name)
        log_audit_event(
            db,
            current_user,
            action="table_create",
            entity_type="table",
            entity_name=request.table_name,
            details={"columns": [column.model_dump() for column in request.columns], "connection": connection_name},
        )
        db.commit()

        table_info = get_table_info(data_db, request.table_name)
        return table_info
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    finally:
        if close_data_db:
            data_db.close()


@router.get("/list", response_model=List[str])
async def list_tables(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_from_header)
):
    """Get list of all tables"""
    data_db, close_data_db, _ = resolve_data_session(db, current_user)
    all_tables = get_all_tables(data_db)
    if close_data_db:
        data_db.close()

    if is_admin(current_user):
        return all_tables

    return [
        table_name
        for table_name in all_tables
        if has_table_permission(db, current_user, table_name, "read")
    ]


@router.get("/{table_name}", response_model=TableInfo)
async def get_table_schema(
    table_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_from_header)
):
    """Get table schema information"""
    data_db, close_data_db, _ = resolve_data_session(db, current_user)
    try:
        require_table_permission(db, current_user, table_name, "read")
        return get_table_info(data_db, table_name)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    finally:
        if close_data_db:
            data_db.close()


@router.post("/import-csv", response_model=ImportResponse)
async def import_csv(
    file: UploadFile = File(...),
    table_name: Optional[str] = Form(None),
    request: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_from_header)
):
    """Import CSV file into table"""
    data_db, close_data_db, connection_name = resolve_data_session(db, current_user)
    try:
        content = await file.read()

        request_table_name, columns_mapping, delimiter, encoding, edited_preview_rows = _parse_import_request(
            table_name=table_name,
            request=request,
        )

        require_table_permission(db, current_user, request_table_name, "write")

        log_audit_event(
            db,
            current_user,
            action="table_import_sync_started",
            entity_type="table",
            entity_name=request_table_name,
            details={"file_name": file.filename, "connection": connection_name},
        )

        result = _execute_import(
            meta_db=db,
            data_db=data_db,
            user_id=current_user.id,
            file_name=file.filename,
            content=content,
            request_table_name=request_table_name,
            columns_mapping=columns_mapping,
            delimiter=delimiter,
            encoding=encoding,
            edited_preview_rows=edited_preview_rows,
        )

        log_audit_event(
            db,
            current_user,
            action="table_import_sync_completed",
            entity_type="table",
            entity_name=request_table_name,
            details={"rows_imported": result.rows_imported, "file_name": file.filename, "connection": connection_name},
        )
        db.commit()

        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}"
        )
    finally:
        if close_data_db:
            data_db.close()


@router.post("/import-csv/async")
async def start_import_csv_async(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    table_name: Optional[str] = Form(None),
    request: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_from_header)
):
    """Start CSV import as background job"""
    try:
        content = await file.read()
        request_table_name, columns_mapping, delimiter, encoding, edited_preview_rows = _parse_import_request(
            table_name=table_name,
            request=request,
        )

        require_table_permission(db, current_user, request_table_name, "write")

        resolved_data_db, should_close_resolved, connection_name = resolve_data_session(db, current_user)
        if should_close_resolved:
            resolved_data_db.close()

        log_audit_event(
            db,
            current_user,
            action="table_import_async_started",
            entity_type="table",
            entity_name=request_table_name,
            details={"file_name": file.filename, "connection": connection_name},
        )
        db.commit()

        job_id = str(uuid.uuid4())
        _set_import_job_state(
            job_id,
            user_id=current_user.id,
            table_name=request_table_name,
            status="queued",
            progress=0,
            message="Задача поставлена в очередь",
        )

        background_tasks.add_task(
            _run_import_job,
            job_id,
            current_user.id,
            file.filename,
            content,
            request_table_name,
            columns_mapping,
            delimiter,
            encoding,
            edited_preview_rows,
        )

        return {
            "job_id": job_id,
            "status": "queued",
            "progress": 0,
            "message": "Задача поставлена в очередь",
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Async import start failed: {str(e)}"
        )


@router.get("/import-csv/jobs/{job_id}")
async def get_import_csv_job_status(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_from_header)
):
    with import_jobs_lock:
        job = import_jobs.get(job_id)

    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import job not found")

    if not is_admin(current_user) and job.get("user_id") != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this import job")

    return {
        "job_id": job_id,
        "status": job.get("status", "unknown"),
        "progress": job.get("progress", 0),
        "message": job.get("message", ""),
        "result": job.get("result"),
    }


@router.post("/import-csv/preview")
async def preview_import_csv(
    file: UploadFile = File(...),
    request: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_from_header)
):
    """Preview CSV before import (first 100 rows)"""
    try:
        encoding = "utf-8"
        delimiter = None
        preview_limit = 100

        if request:
            try:
                payload: Any = json.loads(request)
                if isinstance(payload, dict):
                    payload_encoding = payload.get("encoding")
                    payload_delimiter = payload.get("delimiter")
                    payload_limit = payload.get("preview_limit")

                    if isinstance(payload_encoding, str) and payload_encoding:
                        encoding = payload_encoding
                    if isinstance(payload_delimiter, str) and payload_delimiter in [",", ";", "\t"]:
                        delimiter = payload_delimiter
                    if isinstance(payload_limit, int) and 1 <= payload_limit <= 1000:
                        preview_limit = payload_limit
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON in request field")

        content = await file.read()
        preview = preview_csv(content, encoding=encoding, delimiter=delimiter, preview_limit=preview_limit)

        return preview
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Preview failed: {str(e)}"
        )


@router.get("/history/list", response_model=List[ImportHistoryResponse])
async def get_import_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_from_header)
):
    """Get import history"""
    if is_admin(current_user):
        history = db.query(ImportHistory).all()
        return history

    history = db.query(ImportHistory).filter(ImportHistory.user_id == current_user.id).all()
    return history


@router.get("/{table_name}/data")
async def get_table_data_endpoint(
    table_name: str,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_from_header)
):
    """Get table data with pagination"""
    data_db, close_data_db, _ = resolve_data_session(db, current_user)
    try:
        require_table_permission(db, current_user, table_name, "read")
        rows, total = get_table_data(data_db, table_name, limit=limit, offset=offset)
        return {
            "data": rows,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    finally:
        if close_data_db:
            data_db.close()


@router.get("/{table_name}/versions", response_model=List[TableVersionResponse])
async def get_table_versions(
    table_name: str,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_from_header)
):
    """Get latest table versions for rollback"""
    require_table_permission(db, current_user, table_name, "read")

    safe_limit = max(1, min(100, limit))
    versions = (
        db.query(TableVersion)
        .filter(TableVersion.table_name == table_name)
        .order_by(TableVersion.id.desc())
        .limit(safe_limit)
        .all()
    )

    return [
        TableVersionResponse(
            id=version.id,
            user_id=version.user_id,
            table_name=version.table_name,
            action=version.action,
            row_count=int((version.version_data or {}).get("row_count", 0)),
            message=(version.version_data or {}).get("message"),
            created_at=version.created_at,
        )
        for version in versions
    ]


@router.post("/{table_name}/rollback/{version_id}", response_model=RollbackResponse)
async def rollback_table_to_version(
    table_name: str,
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_from_header)
):
    """Rollback table data to selected version snapshot"""
    data_db, close_data_db, connection_name = resolve_data_session(db, current_user)
    try:
        require_table_permission(db, current_user, table_name, "write")

        version = (
            db.query(TableVersion)
            .filter(TableVersion.id == version_id, TableVersion.table_name == table_name)
            .first()
        )
        if not version:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")

        version_data = version.version_data or {}
        snapshot_rows = version_data.get("rows")
        if not isinstance(snapshot_rows, list):
            raise ValueError("Version data does not contain valid rows snapshot")

        _create_table_version_snapshot(
            meta_db=db,
            data_db=data_db,
            user_id=current_user.id,
            table_name=table_name,
            action="rollback_before",
            message=f"Before rollback to version {version_id}",
        )

        restored_rows = restore_table_snapshot(data_db, table_name, snapshot_rows)

        db.add(TableVersion(
            user_id=current_user.id,
            table_name=table_name,
            action="rollback_applied",
            version_data={
                "source_version_id": version_id,
                "row_count": restored_rows,
                "message": f"Rollback applied from version {version_id}",
            },
        ))
        log_audit_event(
            db,
            current_user,
            action="table_rollback",
            entity_type="table",
            entity_name=table_name,
            details={"source_version_id": version_id, "restored_rows": restored_rows, "connection": connection_name},
        )
        db.commit()

        return RollbackResponse(
            success=True,
            table_name=table_name,
            source_version_id=version_id,
            restored_rows=restored_rows,
            message=f"Rollback to version {version_id} applied",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    finally:
        if close_data_db:
            data_db.close()


@router.post("/{table_name}/rows")
async def create_table_row(
    table_name: str,
    request: RowCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_from_header)
):
    """Create a single row in table"""
    data_db, close_data_db, connection_name = resolve_data_session(db, current_user)
    try:
        require_table_permission(db, current_user, table_name, "write")
        _create_table_version_snapshot(
            meta_db=db,
            data_db=data_db,
            user_id=current_user.id,
            table_name=table_name,
            action="row_create_before",
            message="Before creating a row",
        )
        row_id = create_row(data_db, table_name, request.values)
        log_audit_event(
            db,
            current_user,
            action="row_create",
            entity_type="table",
            entity_name=table_name,
            details={"row_id": row_id, "connection": connection_name},
        )
        db.commit()
        return {"message": "Row created", "row_id": row_id}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    finally:
        if close_data_db:
            data_db.close()


@router.put("/{table_name}/rows/{row_id}")
async def update_table_row(
    table_name: str,
    row_id: int,
    request: RowUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_from_header)
):
    """Update a single row in table"""
    data_db, close_data_db, connection_name = resolve_data_session(db, current_user)
    try:
        require_table_permission(db, current_user, table_name, "write")
        _create_table_version_snapshot(
            meta_db=db,
            data_db=data_db,
            user_id=current_user.id,
            table_name=table_name,
            action="row_update_before",
            message=f"Before updating row {row_id}",
        )
        updated = update_row(data_db, table_name, row_id, request.values)
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Row not found")
        log_audit_event(
            db,
            current_user,
            action="row_update",
            entity_type="table",
            entity_name=table_name,
            details={"row_id": row_id, "connection": connection_name},
        )
        db.commit()
        return {"message": "Row updated", "row_id": row_id}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    finally:
        if close_data_db:
            data_db.close()


@router.delete("/{table_name}/rows")
async def delete_table_rows(
    table_name: str,
    request: RowsDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_from_header)
):
    """Delete selected rows in table"""
    data_db, close_data_db, connection_name = resolve_data_session(db, current_user)
    try:
        require_table_permission(db, current_user, table_name, "write")
        _create_table_version_snapshot(
            meta_db=db,
            data_db=data_db,
            user_id=current_user.id,
            table_name=table_name,
            action="row_delete_before",
            message=f"Before deleting rows: {request.row_ids}",
        )
        deleted = delete_rows(data_db, table_name, request.row_ids)
        log_audit_event(
            db,
            current_user,
            action="row_delete",
            entity_type="table",
            entity_name=table_name,
            details={"row_ids": request.row_ids, "deleted_count": deleted, "connection": connection_name},
        )
        db.commit()
        return {"message": "Rows deleted", "deleted_count": deleted}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    finally:
        if close_data_db:
            data_db.close()


@router.delete("/{table_name}")
async def delete_table_endpoint(
    table_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_from_header)
):
    """Delete a table"""
    data_db, close_data_db, connection_name = resolve_data_session(db, current_user)
    try:
        require_table_permission(db, current_user, table_name, "delete")
        drop_table(data_db, table_name)

        db.query(TablePermission).filter(TablePermission.table_name == table_name).delete()
        db.query(TableSchema).filter(TableSchema.table_name == table_name).delete()
        db.query(TableVersion).filter(TableVersion.table_name == table_name).delete()
        log_audit_event(
            db,
            current_user,
            action="table_delete",
            entity_type="table",
            entity_name=table_name,
            details={"connection": connection_name},
        )
        db.commit()

        return {"message": f"Table '{table_name}' deleted successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    finally:
        if close_data_db:
            data_db.close()


@router.get("/{table_name}/export")
async def export_table_csv(
    table_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_from_header)
):
    """Export table data to CSV file"""
    data_db, close_data_db, _ = resolve_data_session(db, current_user)
    try:
        require_table_permission(db, current_user, table_name, "read")
        # Get table description for column names
        table_info = get_table_info(data_db, table_name)
        
        # Get all data (without pagination for export)
        rows, _ = get_table_data(data_db, table_name, limit=999999, offset=0)
        
        # Create CSV in memory
        output = io.StringIO()
        
        if rows:
            # Get column names from first row + id
            column_names = ["id"] + [col.name for col in table_info.columns]
            writer = csv.DictWriter(output, fieldnames=column_names)
            writer.writeheader()
            writer.writerows(rows)
        
        # Convert to bytes
        csv_bytes = output.getvalue().encode()
        
        return StreamingResponse(
            iter([csv_bytes]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={table_name}.csv"}
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )
    finally:
        if close_data_db:
            data_db.close()
