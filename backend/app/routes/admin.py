from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models import User, TablePermission, AuditLog, get_db
from app.routes.auth import get_current_user
from app.schemas.schemas import (
    AuditLogResponse,
    PermissionBlockRequest,
    PermissionUpdateRequest,
    TablePermissionResponse,
    UserSummaryResponse,
)
from app.utils.audit import log_audit_event

router = APIRouter(prefix="/api/admin", tags=["Admin"])


def get_admin_from_header(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        token = authorization.replace("Bearer ", "")
        username = get_current_user(token)
    except HTTPException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if (user.role or "operator") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    return user


@router.get("/users", response_model=List[UserSummaryResponse])
async def list_users(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_from_header),
):
    return db.query(User).order_by(User.username.asc()).all()


@router.get("/permissions/{table_name}", response_model=List[TablePermissionResponse])
async def get_table_permissions(
    table_name: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_from_header),
):
    permissions = db.query(TablePermission).filter(TablePermission.table_name == table_name).all()

    user_map = {
        user.id: user.username
        for user in db.query(User).filter(User.id.in_([perm.user_id for perm in permissions])).all()
    }

    return [
        TablePermissionResponse(
            username=user_map.get(permission.user_id, f"user:{permission.user_id}"),
            table_name=permission.table_name,
            can_read=bool(permission.can_read),
            can_write=bool(permission.can_write),
            can_alter=bool(permission.can_alter),
            can_delete=bool(permission.can_delete),
            is_owner=bool(permission.is_owner),
            blocked_until=permission.blocked_until,
        )
        for permission in permissions
    ]


@router.post("/permissions/grant")
async def grant_or_update_permission(
    request: PermissionUpdateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_from_header),
):
    target_user = db.query(User).filter(User.username == request.username).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user not found")

    permission = db.query(TablePermission).filter(
        TablePermission.user_id == target_user.id,
        TablePermission.table_name == request.table_name,
    ).first()

    if not permission:
        permission = TablePermission(
            user_id=target_user.id,
            table_name=request.table_name,
            created_at=datetime.utcnow(),
        )
        db.add(permission)

    permission.can_read = 1 if request.can_read else 0
    permission.can_write = 1 if request.can_write else 0
    permission.can_alter = 1 if request.can_alter else 0
    permission.can_delete = 1 if request.can_delete else 0
    permission.is_owner = 1 if request.is_owner else 0
    permission.updated_at = datetime.utcnow()

    log_audit_event(
        db,
        admin_user,
        action="admin_permission_grant",
        entity_type="table_permission",
        entity_name=request.table_name,
        details={
            "target_username": request.username,
            "can_read": request.can_read,
            "can_write": request.can_write,
            "can_alter": request.can_alter,
            "can_delete": request.can_delete,
            "is_owner": request.is_owner,
        },
    )

    db.commit()

    return {
        "message": "Permissions updated",
        "username": request.username,
        "table_name": request.table_name,
    }


@router.post("/permissions/revoke")
async def revoke_permission(
    request: PermissionUpdateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_from_header),
):
    target_user = db.query(User).filter(User.username == request.username).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user not found")

    deleted = db.query(TablePermission).filter(
        TablePermission.user_id == target_user.id,
        TablePermission.table_name == request.table_name,
    ).delete()

    if deleted > 0:
        log_audit_event(
            db,
            admin_user,
            action="admin_permission_revoke",
            entity_type="table_permission",
            entity_name=request.table_name,
            details={
                "target_username": request.username,
            },
        )

    db.commit()

    if deleted == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")

    return {
        "message": "Permissions revoked",
        "username": request.username,
        "table_name": request.table_name,
    }


@router.post("/permissions/block")
async def block_user_table_access(
    request: PermissionBlockRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_from_header),
):
    target_user = db.query(User).filter(User.username == request.username).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user not found")

    permission = db.query(TablePermission).filter(
        TablePermission.user_id == target_user.id,
        TablePermission.table_name == request.table_name,
    ).first()
    if not permission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")

    permission.blocked_until = request.blocked_until or datetime.utcnow()
    permission.updated_at = datetime.utcnow()

    log_audit_event(
        db,
        admin_user,
        action="admin_permission_block",
        entity_type="table_permission",
        entity_name=request.table_name,
        details={
            "target_username": request.username,
            "blocked_until": permission.blocked_until.isoformat() if permission.blocked_until else None,
        },
    )

    db.commit()

    return {
        "message": "User access blocked for table",
        "username": request.username,
        "table_name": request.table_name,
        "blocked_until": permission.blocked_until,
    }


@router.post("/permissions/unblock")
async def unblock_user_table_access(
    request: PermissionBlockRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_from_header),
):
    target_user = db.query(User).filter(User.username == request.username).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user not found")

    permission = db.query(TablePermission).filter(
        TablePermission.user_id == target_user.id,
        TablePermission.table_name == request.table_name,
    ).first()
    if not permission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")

    permission.blocked_until = None
    permission.updated_at = datetime.utcnow()

    log_audit_event(
        db,
        admin_user,
        action="admin_permission_unblock",
        entity_type="table_permission",
        entity_name=request.table_name,
        details={
            "target_username": request.username,
        },
    )

    db.commit()

    return {
        "message": "User access unblocked for table",
        "username": request.username,
        "table_name": request.table_name,
    }


@router.get("/audit", response_model=List[AuditLogResponse])
async def list_audit_logs(
    limit: int = 100,
    username: Optional[str] = None,
    action: Optional[str] = None,
    table_name: Optional[str] = None,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_from_header),
):
    safe_limit = max(1, min(500, limit))

    query = db.query(AuditLog)
    if username:
        query = query.filter(AuditLog.username == username)
    if action:
        query = query.filter(AuditLog.action == action)
    if table_name:
        query = query.filter(AuditLog.entity_name == table_name)

    return (
        query.order_by(desc(AuditLog.created_at))
        .limit(safe_limit)
        .all()
    )
