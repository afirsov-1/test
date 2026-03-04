from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models import AuditLog, User


def log_audit_event(
    db: Session,
    user: User,
    action: str,
    entity_type: str,
    entity_name: Optional[str] = None,
    status: str = "success",
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """Best-effort audit log writer"""
    try:
        db.add(
            AuditLog(
                user_id=user.id,
                username=user.username,
                action=action,
                entity_type=entity_type,
                entity_name=entity_name,
                status=status,
                details=details,
            )
        )
    except Exception:
        pass
