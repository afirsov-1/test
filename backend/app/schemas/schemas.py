from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import List, Optional, Any, Dict


# ----- Authentication schemas -----
class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    active_connection_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ----- CSV Import schemas -----
class ColumnDefinition(BaseModel):
    name: str
    type: str  # varchar, integer, decimal, date, timestamp, boolean
    nullable: bool = True
    unique: bool = False
    default: Optional[Any] = None
    max_length: Optional[int] = None


class CreateTableRequest(BaseModel):
    table_name: str = Field(..., min_length=1, max_length=100)
    columns: List[ColumnDefinition]


class CSVValidationError(BaseModel):
    row: int
    error: str
    suggested_fix: str


class CSVImportRequest(BaseModel):
    table_name: str
    columns_mapping: Dict[str, str]  # CSV column -> DB column


class ImportResponse(BaseModel):
    success: bool
    rows_imported: int
    errors: List[CSVValidationError] = []
    warnings: List[str] = []
    message: str


class ColumnInfo(BaseModel):
    name: str
    type: str
    nullable: bool
    max_length: Optional[int] = None


class TableInfo(BaseModel):
    name: str
    columns: List[ColumnInfo]


# ----- Import history -----
class ImportHistoryResponse(BaseModel):
    id: int
    table_name: str
    file_name: str
    rows_imported: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class PermissionUpdateRequest(BaseModel):
    username: str
    table_name: str
    can_read: bool = False
    can_write: bool = False
    can_alter: bool = False
    can_delete: bool = False
    is_owner: bool = False


class PermissionBlockRequest(BaseModel):
    username: str
    table_name: str
    blocked_until: Optional[datetime] = None


class UserSummaryResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: int

    class Config:
        from_attributes = True


class TablePermissionResponse(BaseModel):
    username: str
    table_name: str
    can_read: bool
    can_write: bool
    can_alter: bool
    can_delete: bool
    is_owner: bool
    blocked_until: Optional[datetime] = None


class RowCreateRequest(BaseModel):
    values: Dict[str, Any]


class RowUpdateRequest(BaseModel):
    values: Dict[str, Any]


class RowsDeleteRequest(BaseModel):
    row_ids: List[int]


class TableVersionResponse(BaseModel):
    id: int
    user_id: int
    table_name: str
    action: str
    row_count: int = 0
    message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RollbackResponse(BaseModel):
    success: bool
    table_name: str
    source_version_id: int
    restored_rows: int
    message: str


class AuditLogResponse(BaseModel):
    id: int
    user_id: int
    username: str
    action: str
    entity_type: str
    entity_name: Optional[str] = None
    status: str
    details: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ConnectionCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    db_type: str = Field(default="postgresql")
    connection_url: str = Field(..., min_length=1)
    is_shared: bool = False


class ConnectionResponse(BaseModel):
    id: int
    name: str
    db_type: str
    is_shared: bool
    is_active: bool
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
