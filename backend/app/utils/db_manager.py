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
    seen_columns = set()
    for col in columns:
        if not is_valid_column_name(col.name):
            raise ValueError(f"Invalid column name '{col.name}'")
        if col.name == "id":
            raise ValueError("Column name 'id' is reserved")
        if col.name in seen_columns:
            raise ValueError(f"Duplicate column name '{col.name}'")
        seen_columns.add(col.name)

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

    if not is_valid_table_name(table_name):
        raise ValueError("Invalid table name")
    
    try:
        # Build INSERT statement
        columns = list(rows[0].keys())
        if not columns:
            return 0

        for col in columns:
            if not is_valid_column_name(col):
                raise ValueError(f"Invalid column name '{col}'")

        col_names = ", ".join(columns)
        placeholders = ", ".join([f":{col}" for col in columns])
        sql = text(f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})")
        
        inserted_count = 0
        for row in rows:
            values = {col: row.get(col) for col in columns}
            db.execute(sql, values)
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


def is_valid_column_name(column_name: str) -> bool:
    """Validate column name (prevent SQL injection)"""
    import re
    return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', column_name))


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


def get_row_count(db: Session, table_name: str) -> int:
    """Get total row count for a table"""
    if not table_exists(db, table_name):
        raise ValueError(f"Table '{table_name}' does not exist")
    
    try:
        result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        count = result.scalar()
        return count or 0
    except Exception as e:
        raise ValueError(f"Failed to get row count: {str(e)}")


def get_table_data(db: Session, table_name: str, limit: int = 100, offset: int = 0) -> tuple[List[Dict[str, Any]], int]:
    """
    Get paginated data from table
    Returns: (rows, total_count)
    """
    if not table_exists(db, table_name):
        raise ValueError(f"Table '{table_name}' does not exist")
    
    try:
        # Get total count
        total = get_row_count(db, table_name)
        
        # Get paginated data
        result = db.execute(
            text(f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT :limit OFFSET :offset"),
            {"limit": limit, "offset": offset}
        )
        
        # Convert rows to dictionaries
        rows = []
        for row in result.fetchall():
            row_dict = dict(row._mapping) if hasattr(row, '_mapping') else dict(zip(result.keys(), row))
            rows.append(row_dict)
        
        return rows, total
    except Exception as e:
        raise ValueError(f"Failed to get table data: {str(e)}")


def create_row(db: Session, table_name: str, values: Dict[str, Any]) -> int:
    """Create a single row and return its id"""
    if not table_exists(db, table_name):
        raise ValueError(f"Table '{table_name}' does not exist")
    if not is_valid_table_name(table_name):
        raise ValueError("Invalid table name")
    if not values:
        raise ValueError("Row values are required")

    columns = [col for col in values.keys() if col != "id"]
    if not columns:
        raise ValueError("At least one editable column is required")

    for col in columns:
        if not is_valid_column_name(col):
            raise ValueError(f"Invalid column name '{col}'")

    col_names = ", ".join(columns)
    placeholders = ", ".join([f":{col}" for col in columns])
    sql = text(f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders}) RETURNING id")

    try:
        result = db.execute(sql, {col: values.get(col) for col in columns})
        new_id = result.scalar()
        db.commit()
        return int(new_id)
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create row: {str(e)}")


def update_row(db: Session, table_name: str, row_id: int, values: Dict[str, Any]) -> bool:
    """Update a row by id"""
    if not table_exists(db, table_name):
        raise ValueError(f"Table '{table_name}' does not exist")
    if not is_valid_table_name(table_name):
        raise ValueError("Invalid table name")
    if row_id <= 0:
        raise ValueError("Invalid row id")
    if not values:
        raise ValueError("Update values are required")

    columns = [col for col in values.keys() if col != "id"]
    if not columns:
        raise ValueError("At least one editable column is required")

    for col in columns:
        if not is_valid_column_name(col):
            raise ValueError(f"Invalid column name '{col}'")

    set_clause = ", ".join([f"{col} = :{col}" for col in columns])
    params = {col: values.get(col) for col in columns}
    params["row_id"] = row_id

    sql = text(f"UPDATE {table_name} SET {set_clause} WHERE id = :row_id")

    try:
        result = db.execute(sql, params)
        db.commit()
        return result.rowcount > 0
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to update row: {str(e)}")


def delete_rows(db: Session, table_name: str, row_ids: List[int]) -> int:
    """Delete multiple rows by ids"""
    if not table_exists(db, table_name):
        raise ValueError(f"Table '{table_name}' does not exist")
    if not is_valid_table_name(table_name):
        raise ValueError("Invalid table name")
    if not row_ids:
        return 0

    normalized_ids = []
    for row_id in row_ids:
        if not isinstance(row_id, int) or row_id <= 0:
            raise ValueError("All row ids must be positive integers")
        normalized_ids.append(row_id)

    deleted = 0
    try:
        sql = text(f"DELETE FROM {table_name} WHERE id = :row_id")
        for row_id in normalized_ids:
            result = db.execute(sql, {"row_id": row_id})
            deleted += result.rowcount or 0
        db.commit()
        return deleted
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to delete rows: {str(e)}")


def get_table_snapshot(db: Session, table_name: str) -> List[Dict[str, Any]]:
    """Get full table snapshot ordered by id asc"""
    if not table_exists(db, table_name):
        raise ValueError(f"Table '{table_name}' does not exist")
    if not is_valid_table_name(table_name):
        raise ValueError("Invalid table name")

    try:
        result = db.execute(text(f"SELECT * FROM {table_name} ORDER BY id ASC"))
        rows = []
        for row in result.fetchall():
            row_dict = dict(row._mapping) if hasattr(row, '_mapping') else dict(zip(result.keys(), row))
            rows.append(row_dict)
        return rows
    except Exception as e:
        raise ValueError(f"Failed to build table snapshot: {str(e)}")


def restore_table_snapshot(db: Session, table_name: str, rows: List[Dict[str, Any]]) -> int:
    """Replace table data with snapshot rows"""
    if not table_exists(db, table_name):
        raise ValueError(f"Table '{table_name}' does not exist")
    if not is_valid_table_name(table_name):
        raise ValueError("Invalid table name")

    normalized_rows = rows or []

    try:
        db.execute(text(f"DELETE FROM {table_name}"))

        restored_count = 0
        if normalized_rows:
            columns = list(normalized_rows[0].keys())
            if not columns:
                raise ValueError("Snapshot rows have no columns")

            for col in columns:
                if not is_valid_column_name(col):
                    raise ValueError(f"Invalid snapshot column '{col}'")

            col_names = ", ".join(columns)
            placeholders = ", ".join([f":{col}" for col in columns])
            sql = text(f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})")

            for row in normalized_rows:
                values = {col: row.get(col) for col in columns}
                db.execute(sql, values)
                restored_count += 1

        sequence_name = db.execute(
            text("SELECT pg_get_serial_sequence(:table_name, 'id')"),
            {"table_name": table_name}
        ).scalar()

        if sequence_name:
            max_id = db.execute(text(f"SELECT COALESCE(MAX(id), 0) FROM {table_name}")).scalar() or 0
            if max_id > 0:
                db.execute(
                    text("SELECT setval(:sequence_name, :max_id, true)"),
                    {"sequence_name": sequence_name, "max_id": int(max_id)}
                )
            else:
                db.execute(
                    text("SELECT setval(:sequence_name, 1, false)"),
                    {"sequence_name": sequence_name}
                )

        db.commit()
        return restored_count
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to restore snapshot: {str(e)}")

