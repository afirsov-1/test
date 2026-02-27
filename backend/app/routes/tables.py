from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from app.schemas.schemas import (
    CreateTableRequest, TableInfo, ImportResponse, CSVImportRequest,
    ImportHistoryResponse
)
from app.models import get_db, ImportHistory, TableSchema
from app.utils.db_manager import (
    create_table, drop_table, get_table_info, get_all_tables, insert_rows
)
from app.utils.csv_handler import parse_csv, validate_csv_against_table_schema
from app.routes.auth import get_current_user

router = APIRouter(prefix="/api/tables", tags=["Tables"])


def get_user_from_header(authorization: Optional[str] = Header(None)) -> str:
    """Extract username from Authorization header"""
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    try:
        token = authorization.replace("Bearer ", "")
        username = get_current_user(token)
        return username
    except HTTPException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


@router.post("/create", response_model=TableInfo)
async def create_new_table(
    request: CreateTableRequest,
    db: Session = Depends(get_db),
    username: str = Depends(get_user_from_header)
):
    """Create a new table in the database"""
    try:
        create_table(db, request.table_name, request.columns)
        table_info = get_table_info(db, request.table_name)
        return table_info
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/list", response_model=List[str])
async def list_tables(
    db: Session = Depends(get_db),
    username: str = Depends(get_user_from_header)
):
    """Get list of all tables"""
    return get_all_tables(db)


@router.get("/{table_name}", response_model=TableInfo)
async def get_table_schema(
    table_name: str,
    db: Session = Depends(get_db),
    username: str = Depends(get_user_from_header)
):
    """Get table schema information"""
    try:
        return get_table_info(db, table_name)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/import-csv", response_model=ImportResponse)
async def import_csv(
    file: UploadFile = File(...),
    table_name: str = None,
    db: Session = Depends(get_db),
    username: str = Depends(get_user_from_header)
):
    """Import CSV file into table"""
    try:
        content = await file.read()
        file_content = content.decode('utf-8', errors='ignore')
        
        headers, rows = parse_csv(file_content)
        
        if not rows:
            raise ValueError("CSV file is empty")
        
        table_info = get_table_info(db, table_name)
        columns_config = {col.name: col.type for col in table_info.columns}
        
        columns_mapping = {header: header for header in headers}
        
        valid_rows, errors = validate_csv_against_table_schema(
            rows,
            columns_config,
            columns_mapping
        )
        
        inserted_count = 0
        if valid_rows:
            inserted_count = insert_rows(db, table_name, valid_rows)
        
        from app.models import User
        user = db.query(User).filter(User.username == username).first()
        
        history = ImportHistory(
            user_id=user.id,
            table_name=table_name,
            file_name=file.filename,
            rows_imported=inserted_count,
            status="success" if not errors else "partial",
            validation_errors=[{"row": e.row, "error": e.error} for e in errors]
        )
        db.add(history)
        db.commit()
        
        return ImportResponse(
            success=len(errors) == 0,
            rows_imported=inserted_count,
            errors=errors,
            warnings=[] if len(errors) == 0 else [f"Found {len(errors)} validation errors"],
            message=f"Successfully imported {inserted_count} rows" if inserted_count > 0 else "No rows imported"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}"
        )


@router.get("/history/list", response_model=List[ImportHistoryResponse])
async def get_import_history(
    db: Session = Depends(get_db),
    username: str = Depends(get_user_from_header)
):
    """Get import history"""
    from app.models import User
    user = db.query(User).filter(User.username == username).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    history = db.query(ImportHistory).filter(ImportHistory.user_id == user.id).all()
    return history

