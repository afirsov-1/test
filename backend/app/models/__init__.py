from sqlalchemy import Column, Integer, String, DateTime, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from app.config import settings

Base = declarative_base()


class User(Base):
    """User model for authentication"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="operator")  # admin | operator
    active_connection_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Integer, default=1)


class ImportHistory(Base):
    """History of CSV imports"""
    __tablename__ = "import_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    table_name = Column(String(255), nullable=False)
    file_name = Column(String(255), nullable=False)
    rows_imported = Column(Integer, default=0)
    validation_errors = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="success")  # success, failed, partial


class TableSchema(Base):
    """Store information about created tables for metadata"""
    __tablename__ = "table_schemas"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    table_name = Column(String(255), nullable=False)
    columns_config = Column(JSON, nullable=False)  # Store column definitions
    created_at = Column(DateTime, default=datetime.utcnow)


class TablePermission(Base):
    """Table-level permissions for RBAC"""
    __tablename__ = "table_permissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    table_name = Column(String(255), nullable=False, index=True)
    can_read = Column(Integer, nullable=False, default=0)
    can_write = Column(Integer, nullable=False, default=0)
    can_alter = Column(Integer, nullable=False, default=0)
    can_delete = Column(Integer, nullable=False, default=0)
    is_owner = Column(Integer, nullable=False, default=0)
    blocked_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class TableVersion(Base):
    """Table data versions for rollback"""
    __tablename__ = "table_versions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    table_name = Column(String(255), nullable=False, index=True)
    action = Column(String(100), nullable=False)
    version_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    """Audit log records for user actions"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    username = Column(String(255), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(100), nullable=False, index=True)
    entity_name = Column(String(255), nullable=True, index=True)
    status = Column(String(50), nullable=False, default="success")
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class DatabaseConnection(Base):
    """Configured external database connections"""
    __tablename__ = "database_connections"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    db_type = Column(String(50), nullable=False, default="postgresql")
    connection_url = Column(String(2048), nullable=False)
    is_shared = Column(Integer, nullable=False, default=0)
    is_active = Column(Integer, nullable=False, default=1)
    created_by = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


# Database connection
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
