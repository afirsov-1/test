import csv
import io
from typing import List, Dict, Any, Tuple
from app.schemas.schemas import CSVValidationError


def detect_delimiter(file_content: str) -> str:
    """Detect CSV delimiter from content sample"""
    sample = file_content[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=[",", ";", "\t"])
        return dialect.delimiter
    except Exception:
        return ","


def decode_csv_bytes(file_bytes: bytes, encoding: str = "utf-8") -> str:
    """Decode CSV bytes with selected encoding and fallbacks"""
    encodings_to_try = [encoding, "utf-8", "cp1251", "latin-1"]
    seen = set()
    for candidate in encodings_to_try:
        if candidate in seen:
            continue
        seen.add(candidate)
        try:
            return file_bytes.decode(candidate)
        except Exception:
            continue
    raise ValueError("Failed to decode CSV with provided encoding")


def parse_csv(file_content: str, delimiter: str = None, max_rows: int = None) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Parse CSV file content and return headers and data
    """
    try:
        resolved_delimiter = delimiter or detect_delimiter(file_content)
        reader = csv.DictReader(io.StringIO(file_content), delimiter=resolved_delimiter)
        headers = reader.fieldnames or []
        rows = []
        for idx, row in enumerate(reader):
            rows.append(row)
            if max_rows is not None and idx + 1 >= max_rows:
                break
        return headers, rows
    except Exception as e:
        raise ValueError(f"Failed to parse CSV: {str(e)}")


def preview_csv(file_bytes: bytes, encoding: str = "utf-8", delimiter: str = None, preview_limit: int = 100):
    """Prepare preview payload for CSV import wizard"""
    file_content = decode_csv_bytes(file_bytes, encoding=encoding)
    resolved_delimiter = delimiter or detect_delimiter(file_content)
    headers, rows = parse_csv(file_content, delimiter=resolved_delimiter, max_rows=preview_limit)
    return {
        "headers": headers,
        "rows": rows,
        "encoding": encoding,
        "delimiter": resolved_delimiter,
        "preview_count": len(rows),
    }


def validate_csv_against_table_schema(
    rows: List[Dict[str, Any]], 
    columns_config: Dict[str, str],
    mapping: Dict[str, str]
) -> Tuple[List[Dict[str, Any]], List[CSVValidationError]]:
    """
    Validate CSV data against table schema
    columns_config: {db_column: data_type}
    mapping: {csv_column: db_column}
    """
    errors = []
    valid_rows = []
    
    for row_idx, row in enumerate(rows, start=2):  # Start from 2 (header is row 1)
        try:
            valid_row = {}
            error_found = False
            
            for csv_col, db_col in mapping.items():
                if csv_col not in row:
                    errors.append(CSVValidationError(
                        row=row_idx,
                        error=f"Column '{csv_col}' not found in CSV",
                        suggested_fix=f"Check CSV header, expected column '{csv_col}'"
                    ))
                    error_found = True
                    continue
                
                value = row[csv_col]
                data_type = columns_config.get(db_col, "varchar")
                
                # Type validation
                validated_value = validate_value(value, data_type, row_idx, db_col, errors)
                if validated_value is not None or (not value and data_type != "required"):
                    valid_row[db_col] = validated_value
                else:
                    error_found = True
            
            if not error_found:
                valid_rows.append(valid_row)
                
        except Exception as e:
            errors.append(CSVValidationError(
                row=row_idx,
                error=str(e),
                suggested_fix="Check data types and formatting"
            ))
    
    return valid_rows, errors


def validate_value(value: Any, data_type: str, row: int, column: str, errors: List[CSVValidationError]) -> Any:
    """Validate and convert value to appropriate type"""
    if not value or value.strip() == "":
        return None
    
    try:
        if data_type == "integer":
            return int(value)
        elif data_type == "decimal":
            return float(value)
        elif data_type == "date":
            # Basic date validation (YYYY-MM-DD)
            if len(value) != 10 or value[4] != '-' or value[7] != '-':
                raise ValueError("Date must be in YYYY-MM-DD format")
            return value
        elif data_type == "boolean":
            if value.lower() in ["true", "1", "yes", "y"]:
                return True
            elif value.lower() in ["false", "0", "no", "n"]:
                return False
            else:
                raise ValueError("Boolean must be true/false")
        else:  # varchar
            return str(value)
    except ValueError as e:
        errors.append(CSVValidationError(
            row=row,
            error=f"Invalid {data_type} value '{value}' in column '{column}': {str(e)}",
            suggested_fix=f"Ensure value is a valid {data_type}"
        ))
        return None
