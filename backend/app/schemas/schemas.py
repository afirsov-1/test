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
