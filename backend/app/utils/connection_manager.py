import threading
from datetime import datetime
from typing import Dict, Tuple

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.models import DatabaseConnection, User
from app.utils.permissions import is_admin

_engine_cache: Dict[str, sessionmaker] = {}
_engine_cache_lock = threading.Lock()


def _validate_connection_url(db_type: str, connection_url: str) -> None:
    if db_type != "postgresql":
        raise ValueError("Only postgresql connections are supported currently")
    if not connection_url.startswith("postgresql://") and not connection_url.startswith("postgresql+psycopg2://"):
        raise ValueError("Invalid PostgreSQL connection URL")


def get_connection_sessionmaker(connection_url: str) -> sessionmaker:
    with _engine_cache_lock:
        if connection_url in _engine_cache:
            return _engine_cache[connection_url]

        engine = create_engine(connection_url, pool_pre_ping=True)
        maker = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        _engine_cache[connection_url] = maker
        return maker


def create_connection(
    db: Session,
    current_user: User,
    name: str,
    db_type: str,
    connection_url: str,
    is_shared: bool,
) -> DatabaseConnection:
    _validate_connection_url(db_type, connection_url)

    existing = db.query(DatabaseConnection).filter(
        DatabaseConnection.created_by == current_user.id,
        DatabaseConnection.name == name,
        DatabaseConnection.is_active == 1,
    ).first()
    if existing:
        raise ValueError("Connection with this name already exists")

    temp_engine = create_engine(connection_url, pool_pre_ping=True)
    temp_session = sessionmaker(autocommit=False, autoflush=False, bind=temp_engine)()
    try:
        temp_session.execute(text("SELECT 1"))
    except Exception as exc:
        raise ValueError(f"Connection validation failed: {str(exc)}")
    finally:
        temp_session.close()
        temp_engine.dispose()

    connection = DatabaseConnection(
        name=name,
        db_type=db_type,
        connection_url=connection_url,
        is_shared=1 if (is_shared and is_admin(current_user)) else 0,
        is_active=1,
        created_by=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(connection)
    db.commit()
    db.refresh(connection)
    return connection


def list_accessible_connections(db: Session, current_user: User):
    query = db.query(DatabaseConnection).filter(DatabaseConnection.is_active == 1)
    if is_admin(current_user):
        return query.order_by(DatabaseConnection.name.asc()).all()

    return (
        query.filter(
            (DatabaseConnection.created_by == current_user.id) |
            (DatabaseConnection.is_shared == 1)
        )
        .order_by(DatabaseConnection.name.asc())
        .all()
    )


def get_connection_for_user(db: Session, current_user: User, connection_id: int) -> DatabaseConnection:
    connection = db.query(DatabaseConnection).filter(
        DatabaseConnection.id == connection_id,
        DatabaseConnection.is_active == 1,
    ).first()
    if not connection:
        raise ValueError("Connection not found")

    if not is_admin(current_user) and connection.created_by != current_user.id and connection.is_shared != 1:
        raise ValueError("No access to selected connection")

    return connection


def test_connection(connection: DatabaseConnection) -> None:
    maker = get_connection_sessionmaker(connection.connection_url)
    session = maker()
    try:
        session.execute(text("SELECT 1"))
    finally:
        session.close()


def set_user_active_connection(db: Session, current_user: User, connection_id: int) -> User:
    connection = get_connection_for_user(db, current_user, connection_id)
    current_user.active_connection_id = connection.id
    db.commit()
    db.refresh(current_user)
    return current_user


def clear_user_active_connection(db: Session, current_user: User) -> User:
    current_user.active_connection_id = None
    db.commit()
    db.refresh(current_user)
    return current_user


def resolve_data_session(db: Session, current_user: User) -> Tuple[Session, bool, str]:
    connection_id = current_user.active_connection_id
    if not connection_id:
        return db, False, "primary"

    try:
        connection = get_connection_for_user(db, current_user, connection_id)
    except ValueError:
        current_user.active_connection_id = None
        db.commit()
        return db, False, "primary"

    maker = get_connection_sessionmaker(connection.connection_url)
    external_session = maker()
    return external_session, True, connection.name
