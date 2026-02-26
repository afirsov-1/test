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
