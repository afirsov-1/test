from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.models import User, DatabaseConnection, get_db
from app.routes.auth import get_current_user
from app.schemas.schemas import ConnectionCreateRequest, ConnectionResponse
from app.utils.audit import log_audit_event
from app.utils.connection_manager import (
    clear_user_active_connection,
    create_connection,
    get_connection_for_user,
    list_accessible_connections,
    set_user_active_connection,
    test_connection,
)

router = APIRouter(prefix="/api/connections", tags=["Connections"])


def get_user_from_header(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    token = authorization.replace("Bearer ", "")
    username = get_current_user(token)
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user


@router.get("/list", response_model=List[ConnectionResponse])
async def list_connections(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_from_header),
):
    return list_accessible_connections(db, current_user)


@router.post("/create", response_model=ConnectionResponse)
async def create_new_connection(
    request: ConnectionCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_from_header),
):
    try:
        connection = create_connection(
            db,
            current_user,
            request.name,
            request.db_type,
            request.connection_url,
            request.is_shared,
        )
        log_audit_event(
            db,
            current_user,
            action="connection_create",
            entity_type="connection",
            entity_name=connection.name,
            details={"connection_id": connection.id, "is_shared": bool(connection.is_shared)},
        )
        db.commit()
        return connection
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/set-active/{connection_id}")
async def set_active_connection(
    connection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_from_header),
):
    try:
        updated_user = set_user_active_connection(db, current_user, connection_id)
        connection = db.query(DatabaseConnection).filter(DatabaseConnection.id == connection_id).first()

        log_audit_event(
            db,
            current_user,
            action="connection_set_active",
            entity_type="connection",
            entity_name=connection.name if connection else str(connection_id),
            details={"connection_id": connection_id},
        )
        db.commit()

        return {
            "message": "Active connection updated",
            "active_connection_id": updated_user.active_connection_id,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/clear-active")
async def clear_active_connection(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_from_header),
):
    updated_user = clear_user_active_connection(db, current_user)
    log_audit_event(
        db,
        current_user,
        action="connection_clear_active",
        entity_type="connection",
        entity_name=None,
    )
    db.commit()

    return {
        "message": "Active connection cleared",
        "active_connection_id": updated_user.active_connection_id,
    }


@router.post("/test/{connection_id}")
async def test_saved_connection(
    connection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_from_header),
):
    try:
        connection = get_connection_for_user(db, current_user, connection_id)
        test_connection(connection)
        return {"success": True, "message": "Connection test successful"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Connection test failed: {str(e)}")
