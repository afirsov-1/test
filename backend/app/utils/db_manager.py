from sqlalchemy import text, inspect
from sqlalchemy.orm import Session
from app.schemas.schemas import ColumnDefinition, TableInfo, ColumnInfo
from typing import List, Dict, Any


def create_table(db: Session, table_name: str, columns: List[ColumnDefinition]) -> bool:
    """
    Create a table dynamically in the database
    """
    if not is_valid_table_name(table_name):
        raise ValueError("Invalid table name")
    
    # Check if table already exists
    if table_exists(db, table_name):
        raise ValueError(f"Table '{table_name}' already exists")
    
    # Build CREATE TABLE statement
    column_defs = []
    for col in columns:
        col_type = get_sql_type(col.type, col.max_length)
        col_def = f"{col.name} {col_type}"
        
        if not col.nullable:
            col_def += " NOT NULL"
        if col.unique:
            col_def += " UNIQUE"
        if col.default is not None:
            col_def += f" DEFAULT {col.default!r}"
        
        column_defs.append(col_def)
    
    if len(column_defs) == 0:
        raise ValueError("Table must have at least one column")
    
    # Add primary key
    column_defs.append("id SERIAL PRIMARY KEY")
    
    sql = f"CREATE TABLE {table_name} (\n  " + ",\n  ".join(column_defs) + "\n)"
    
    try:
        db.execute(text(sql))
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create table: {str(e)}")


def drop_table(db: Session, table_name: str) -> bool:
    """Drop a table"""
    if not is_valid_table_name(table_name):
        raise ValueError("Invalid table name")
    
    if not table_exists(db, table_name):
        raise ValueError(f"Table '{table_name}' does not exist")
    
    try:
        db.execute(text(f"DROP TABLE {table_name}"))
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to drop table: {str(e)}")


def table_exists(db: Session, table_name: str) -> bool:
    """Check if table exists"""
    try:
        inspector = inspect(db.get_bind())
        return table_name in inspector.get_table_names()
    except:
        return False


def get_table_info(db: Session, table_name: str) -> TableInfo:
    """Get table structure information"""
    if not table_exists(db, table_name):
        raise ValueError(f"Table '{table_name}' does not exist")
    
    try:
        inspector = inspect(db.get_bind())
        columns_info = inspector.get_columns(table_name)
        
        columns = []
        for col in columns_info:
            if col['name'] != 'id':  # Skip auto-generated id
                columns.append(ColumnInfo(
                    name=col['name'],
                    type=str(col['type']),
                    nullable=col['nullable'],
                    max_length=getattr(col['type'], 'length', None)
                ))
        
        return TableInfo(name=table_name, columns=columns)
    except Exception as e:
        raise ValueError(f"Failed to get table info: {str(e)}")


def get_all_tables(db: Session) -> List[str]:
    """Get list of all tables"""
    try:
        inspector = inspect(db.get_bind())
        tables = inspector.get_table_names()
        # Filter out system tables
        return [t for t in tables if not t.startswith('sqlite_') and not t.startswith('information_schema')]
    except:
        return []


def insert_rows(db: Session, table_name: str, rows: List[Dict[str, Any]]) -> int:
    """Insert rows into table"""
    if not table_exists(db, table_name):
        raise ValueError(f"Table '{table_name}' does not exist")
    
    if not rows:
        return 0
    
    try:
        # Build INSERT statement
        columns = list(rows[0].keys())
        col_names = ", ".join(columns)
        
        inserted_count = 0
        for row in rows:
            placeholders = ", ".join([f":%s" % col for col in columns])
            values = [row.get(col) for col in columns]
            
            # Use raw SQL for insert
            sql = f"INSERT INTO {table_name} ({col_names}) VALUES ({', '.join(['%s'] * len(columns))})"
            db.execute(text(sql), {f"param_{i}": v for i, v in enumerate(values)})
            inserted_count += 1
        
        db.commit()
        return inserted_count
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to insert rows: {str(e)}")


def is_valid_table_name(table_name: str) -> bool:
    """Validate table name (prevent SQL injection)"""
    import re
    # Allow only alphanumeric and underscore, must start with letter or underscore
    return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name))


def get_sql_type(python_type: str, max_length: int = None) -> str:
    """Convert Python type to SQL type"""
    type_mapping = {
        "varchar": f"VARCHAR({max_length or 255})",
        "integer": "INTEGER",
        "decimal": "DECIMAL(10, 2)",
        "date": "DATE",
        "timestamp": "TIMESTAMP",
        "boolean": "BOOLEAN",
        "text": "TEXT"
    }
    return type_mapping.get(python_type, "VARCHAR(255)")
