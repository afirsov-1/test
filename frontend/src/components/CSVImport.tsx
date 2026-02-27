import React, { useState, useEffect } from 'react';
import { tableService } from '../services/api';
import '../styles/csvImport.css';

interface CSVImportProps {
  tables: string[];
}

interface ValidationError {
  row: number;
  error: string;
  suggested_fix: string;
}

const CSVImport: React.FC<CSVImportProps> = ({ tables }) => {
  const [selectedTable, setSelectedTable] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [columnsMapping, setColumnsMapping] = useState<Record<string, string>>({});
  const [csvHeaders, setCsvHeaders] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [validationErrors, setValidationErrors] = useState<ValidationError[]>([]);
  const [tableColumns, setTableColumns] = useState<string[]>([]);

  // Get table columns when table is selected
  useEffect(() => {
    if (selectedTable) {
      fetchTableSchema();
    }
  }, [selectedTable]);

  const fetchTableSchema = async () => {
    try {
      const response = await tableService.getTableSchema(selectedTable);
      const columns = response.data.columns.map((col: any) => col.name);
      setTableColumns(columns);
    } catch (err: any) {
      setError('Failed to get table schema');
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      if (selectedFile.type !== 'text/csv' && !selectedFile.name.endsWith('.csv')) {
        setError('Please select a CSV file');
        return;
      }

      setFile(selectedFile);
      setError('');
      
      // Parse CSV headers
      const reader = new FileReader();
      reader.onload = (event) => {
        const content = event.target?.result as string;
        const lines = content.split('\n');
        const headers = lines[0].split(',').map((h) => h.trim());
        setCsvHeaders(headers);
        
        // Initialize mapping
        const mapping: Record<string, string> = {};
        headers.forEach((header) => {
          mapping[header] = '';
        });
        setColumnsMapping(mapping);
      };
      reader.readAsText(selectedFile);
    }
  };

  const handleMappingChange = (csvColumn: string, dbColumn: string) => {
    setColumnsMapping({
      ...columnsMapping,
      [csvColumn]: dbColumn,
    });
  };

  const handleImport = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!file || !selectedTable) {
      setError('Please select a file and table');
      return;
    }

    // Check if all columns are mapped
    const unmappedColumns = Object.values(columnsMapping).filter((v) => !v);
    if (unmappedColumns.length > 0) {
      setError('All columns must be mapped');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');
    setValidationErrors([]);

    try {
      const response = await tableService.importCSV(file, selectedTable, columnsMapping);
      
      if (response.data.errors.length > 0) {
        setValidationErrors(response.data.errors);
        setError(`Import completed with ${response.data.errors.length} errors`);
      } else {
        setSuccess(`Successfully imported ${response.data.rows_imported} rows`);
        setFile(null);
        setSelectedTable('');
        setCsvHeaders([]);
        setColumnsMapping({});
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Import failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="csv-import-card">
      <h2>Импорт CSV</h2>

      <form onSubmit={handleImport}>
        <div className="form-group">
          <label htmlFor="table-select">Выберите таблицу</label>
          <select
            id="table-select"
            value={selectedTable}
            onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setSelectedTable(e.target.value)}
            required
          >
            <option value="">-- Выберите таблицу --</option>
            {tables.map((table) => (
              <option key={table} value={table}>
                {table}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="csv-file">Загрузите CSV файл</label>
          <input
            id="csv-file"
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            required
          />
        </div>

        {csvHeaders.length > 0 && tableColumns.length > 0 && (
          <div className="mapping-section">
            <h3>Сопоставление колонок</h3>
            {csvHeaders.map((csvHeader) => (
              <div key={csvHeader} className="mapping-row">
                <label className="csv-column">{csvHeader} (CSV)</label>
                <select
                  value={columnsMapping[csvHeader] || ''}
                  onChange={(e) => handleMappingChange(csvHeader, e.target.value)}
                  required
                >
                  <option value="">-- Выберите колонку --</option>
                  {tableColumns.map((col) => (
                    <option key={col} value={col}>
                      {col}
                    </option>
                  ))}
                </select>
              </div>
            ))}
          </div>
        )}

        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}

        <button type="submit" disabled={loading} className="btn btn-primary">
          {loading ? 'Загрузка...' : 'Импортировать'}
        </button>
      </form>

      {validationErrors.length > 0 && (
        <div className="validation-errors">
          <h3>Ошибки валидации</h3>
          <div className="errors-list">
            {validationErrors.slice(0, 10).map((error, idx) => (
              <div key={idx} className="error-item">
                <p className="error-row">Строка {error.row}:</p>
                <p className="error-text">{error.error}</p>
                <p className="error-fix">💡 Решение: {error.suggested_fix}</p>
              </div>
            ))}
            {validationErrors.length > 10 && (
              <p className="more-errors">...и еще {validationErrors.length - 10} ошибок</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default CSVImport;
