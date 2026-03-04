from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models import User, TablePermission


def get_user_by_username(db: Session, username: str) -> User:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def is_admin(user: User) -> bool:
    return (user.role or "operator") == "admin"


def ensure_owner_permissions(db: Session, user: User, table_name: str) -> None:
    permission = db.query(TablePermission).filter(
        TablePermission.user_id == user.id,
        TablePermission.table_name == table_name
    ).first()

    can_delete = 1 if is_admin(user) else 0

    if permission:
        permission.can_read = 1
        permission.can_write = 1
        permission.can_alter = 1
        permission.can_delete = can_delete
        permission.is_owner = 1
        permission.blocked_until = None
        permission.updated_at = datetime.utcnow()
    else:
        permission = TablePermission(
            user_id=user.id,
            table_name=table_name,
            can_read=1,
            can_write=1,
            can_alter=1,
            can_delete=can_delete,
            is_owner=1,
            blocked_until=None,
        )
        db.add(permission)


def has_table_permission(db: Session, user: User, table_name: str, permission: str) -> bool:
    if is_admin(user):
        return True

    table_permission = db.query(TablePermission).filter(
        TablePermission.user_id == user.id,
        TablePermission.table_name == table_name
    ).first()

    if not table_permission:
        return False

    if table_permission.blocked_until and table_permission.blocked_until > datetime.utcnow():
        return False

    permissions_map = {
        "read": table_permission.can_read,
        "write": table_permission.can_write,
        "alter": table_permission.can_alter,
        "delete": table_permission.can_delete,
    }
    return bool(permissions_map.get(permission, 0))


def require_table_permission(db: Session, user: User, table_name: str, permission: str) -> None:
    if not has_table_permission(db, user, table_name, permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: missing '{permission}' permission for table '{table_name}'"
        )
