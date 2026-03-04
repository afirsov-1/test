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

interface ImportJobState {
  jobId: string;
  status: 'queued' | 'running' | 'completed' | 'failed' | 'unknown';
  progress: number;
  message: string;
}

type WizardStep = 1 | 2;

const CSVImport: React.FC<CSVImportProps> = ({ tables }) => {
  const [step, setStep] = useState<WizardStep>(1);
  const [selectedTable, setSelectedTable] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [columnsMapping, setColumnsMapping] = useState<Record<string, string>>({});
  const [csvHeaders, setCsvHeaders] = useState<string[]>([]);
  const [previewRows, setPreviewRows] = useState<Record<string, any>[]>([]);
  const [delimiterMode, setDelimiterMode] = useState<'auto' | ',' | ';' | '\t'>('auto');
  const [resolvedDelimiter, setResolvedDelimiter] = useState<string>('');
  const [encoding, setEncoding] = useState<string>('utf-8');
  const [useEditedPreviewRows, setUseEditedPreviewRows] = useState(false);
  const [useAsyncImport, setUseAsyncImport] = useState(true);
  const [importJob, setImportJob] = useState<ImportJobState | null>(null);
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

  useEffect(() => {
    if (!importJob?.jobId) {
      return;
    }

    if (importJob.status === 'completed' || importJob.status === 'failed') {
      return;
    }

    const intervalId = window.setInterval(async () => {
      try {
        const response = await tableService.getImportJobStatus(importJob.jobId);
        const payload = response.data;

        setImportJob({
          jobId: payload.job_id,
          status: payload.status,
          progress: payload.progress ?? 0,
          message: payload.message || '',
        });

        if (payload.status === 'completed' && payload.result) {
          const result = payload.result;
          if (Array.isArray(result.errors) && result.errors.length > 0) {
            setValidationErrors(result.errors);
            setError(`Импорт завершен с ошибками: ${result.errors.length}`);
          } else {
            setSuccess(`Успешно импортировано строк: ${result.rows_imported ?? 0}`);
          }

          setFile(null);
          setSelectedTable('');
          setCsvHeaders([]);
          setPreviewRows([]);
          setColumnsMapping({});
          setStep(1);
          setUseEditedPreviewRows(false);
          setLoading(false);
        }

        if (payload.status === 'failed') {
          setError(payload.message || 'Асинхронный импорт завершился ошибкой');
          setLoading(false);
        }
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Ошибка получения статуса импорта');
        setLoading(false);
      }
    }, 1500);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [importJob?.jobId, importJob?.status]);

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
        setError('Пожалуйста, выберите CSV файл');
        return;
      }

      setFile(selectedFile);
      setError('');
      setSuccess('');
      setStep(1);
      setCsvHeaders([]);
      setPreviewRows([]);
      setColumnsMapping({});
      setResolvedDelimiter('');
    }
  };

  const runPreview = async () => {
    if (!file || !selectedTable) {
      setError('Сначала выберите таблицу и файл');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');
    setValidationErrors([]);

    try {
      const response = await tableService.previewCSV(file, {
        encoding,
        delimiter: delimiterMode === 'auto' ? undefined : delimiterMode,
        preview_limit: 100,
      });

      const headers = response.data.headers || [];
      const rows = response.data.rows || [];
      setCsvHeaders(headers);
      setPreviewRows(rows);
      setResolvedDelimiter(response.data.delimiter || '');

      const mapping: Record<string, string> = {};
      headers.forEach((header: string) => {
        mapping[header] = tableColumns.includes(header) ? header : '';
      });
      setColumnsMapping(mapping);
      setStep(2);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка предпросмотра CSV');
    } finally {
      setLoading(false);
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
      setError('Пожалуйста, выберите файл и таблицу');
      return;
    }

    // Check if all columns are mapped
    const unmappedColumns = Object.values(columnsMapping).filter((v) => !v);
    if (unmappedColumns.length > 0) {
      setError('Необходимо сопоставить все колонки CSV');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');
    setValidationErrors([]);

    try {
      const importOptions = {
        delimiter: delimiterMode === 'auto' ? resolvedDelimiter || undefined : delimiterMode,
        encoding,
        edited_preview_rows: useEditedPreviewRows ? previewRows : undefined,
      };

      if (useAsyncImport) {
        const response = await tableService.startImportJob(file, selectedTable, columnsMapping, importOptions);
        setImportJob({
          jobId: response.data.job_id,
          status: response.data.status,
          progress: response.data.progress ?? 0,
          message: response.data.message || 'Задача создана',
        });
        setSuccess('Импорт запущен в фоне. Статус обновляется автоматически.');
        return;
      }

      const response = await tableService.importCSV(file, selectedTable, columnsMapping, importOptions);
      
      if (response.data.errors.length > 0) {
        setValidationErrors(response.data.errors);
        setError(`Импорт завершен с ошибками: ${response.data.errors.length}`);
      } else {
        setSuccess(`Успешно импортировано строк: ${response.data.rows_imported}`);
        setFile(null);
        setSelectedTable('');
        setCsvHeaders([]);
        setPreviewRows([]);
        setColumnsMapping({});
        setStep(1);
        setUseEditedPreviewRows(false);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Импорт не выполнен');
    } finally {
      if (!useAsyncImport) {
        setLoading(false);
      }
    }
  };

  const handlePreviewCellChange = (rowIndex: number, column: string, value: string) => {
    setPreviewRows((prev) => {
      const next = [...prev];
      next[rowIndex] = { ...next[rowIndex], [column]: value };
      return next;
    });
  };

  return (
    <div className="csv-import-card">
      <h2>Импорт CSV — мастер</h2>

      <div className="wizard-steps">
        <div className={`wizard-step ${step === 1 ? 'active' : ''}`}>1. Файл и параметры</div>
        <div className={`wizard-step ${step === 2 ? 'active' : ''}`}>2. Маппинг и предпросмотр</div>
      </div>

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

        <div className="settings-grid">
          <div className="form-group">
            <label htmlFor="delimiter">Разделитель</label>
            <select
              id="delimiter"
              value={delimiterMode}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setDelimiterMode(e.target.value as 'auto' | ',' | ';' | '\t')}
            >
              <option value="auto">Авто</option>
              <option value=",">Запятая (,)</option>
              <option value=";">Точка с запятой (;)</option>
              <option value="\t">Табуляция (\t)</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="encoding">Кодировка</label>
            <select
              id="encoding"
              value={encoding}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setEncoding(e.target.value)}
            >
              <option value="utf-8">UTF-8</option>
              <option value="cp1251">Windows-1251</option>
              <option value="latin-1">Latin-1</option>
            </select>
          </div>
        </div>

        <div className="wizard-actions">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={runPreview}
            disabled={loading || !file || !selectedTable}
          >
            {loading ? 'Подготовка...' : 'Показать предпросмотр (100 строк)'}
          </button>
          {resolvedDelimiter && (
            <span className="detected-meta">Определён разделитель: <strong>{resolvedDelimiter === '\t' ? 'TAB' : resolvedDelimiter}</strong></span>
          )}
        </div>

        {step === 2 && csvHeaders.length > 0 && tableColumns.length > 0 && (
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

            <h3>Предпросмотр (редактируемый)</h3>
            <div className="preview-note">
              Можно редактировать значения прямо в таблице перед импортом.
            </div>
            <div className="preview-table-wrapper">
              <table className="preview-table">
                <thead>
                  <tr>
                    {csvHeaders.map((header) => (
                      <th key={`h-${header}`}>{header}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {previewRows.slice(0, 100).map((row, rowIndex) => (
                    <tr key={`r-${rowIndex}`}>
                      {csvHeaders.map((header) => (
                        <td key={`c-${rowIndex}-${header}`}>
                          <input
                            className="preview-input"
                            value={row[header] ?? ''}
                            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                              handlePreviewCellChange(rowIndex, header, e.target.value)
                            }
                          />
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <label className="checkbox apply-preview-checkbox">
              <input
                type="checkbox"
                checked={useEditedPreviewRows}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setUseEditedPreviewRows(e.target.checked)}
              />
              Импортировать только отредактированный предпросмотр (первые 100 строк)
            </label>

            <label className="checkbox apply-preview-checkbox">
              <input
                type="checkbox"
                checked={useAsyncImport}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setUseAsyncImport(e.target.checked)}
              />
              Асинхронный импорт с прогрессом
            </label>
          </div>
        )}

        {importJob && (
          <div className="job-status-panel">
            <div className="job-status-head">
              <span>Статус задачи: <strong>{importJob.status}</strong></span>
              <span>{importJob.progress}%</span>
            </div>
            <div className="job-progress-track">
              <div className="job-progress-fill" style={{ width: `${Math.max(0, Math.min(100, importJob.progress))}%` }} />
            </div>
            <div className="job-status-message">{importJob.message}</div>
          </div>
        )}

        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}

        <button type="submit" disabled={loading || step !== 2 || importJob?.status === 'running' || importJob?.status === 'queued'} className="btn btn-primary">
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
