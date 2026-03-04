import { useState, useEffect } from 'react';
import { tableService } from '../services/api';
import '../styles/viewTable.css';

interface ViewTableProps {
  tables: string[];
  onTablesChange: () => void;
}

interface TableData {
  data: any[];
  total: number;
  limit: number;
  offset: number;
}

interface TableVersion {
  id: number;
  user_id: number;
  table_name: string;
  action: string;
  row_count: number;
  message?: string;
  created_at: string;
}

const ViewTable: React.FC<ViewTableProps> = ({ tables, onTablesChange }): JSX.Element => {
  const [selectedTable, setSelectedTable] = useState('');
  const [tableData, setTableData] = useState<TableData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [currentPage, setCurrentPage] = useState(0);
  const [pageSize] = useState(10);
  const [searchTerm, setSearchTerm] = useState('');
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [editingRowId, setEditingRowId] = useState<number | null>(null);
  const [editValues, setEditValues] = useState<Record<string, any>>({});
  const [newRowValues, setNewRowValues] = useState<Record<string, any>>({});
  const [selectedRowIds, setSelectedRowIds] = useState<number[]>([]);
  const [versions, setVersions] = useState<TableVersion[]>([]);
  const [selectedVersionId, setSelectedVersionId] = useState<string>('');

  useEffect(() => {
    if (selectedTable) {
      loadTableData(0);
      loadVersions(selectedTable);
    }
  }, [selectedTable]);

  const loadTableData = async (page: number) => {
    if (!selectedTable) return;

    setLoading(true);
    setError('');
    setSuccess('');
    try {
      const response = await tableService.getTableData(selectedTable, pageSize, page * pageSize);
      setTableData(response.data);
      setCurrentPage(page);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка при загрузке данных');
    } finally {
      setLoading(false);
    }
  };

  const loadVersions = async (tableName: string) => {
    try {
      const response = await tableService.getTableVersions(tableName, 30);
      setVersions(response.data || []);
      setSelectedVersionId((prev) => {
        if (prev) {
          return prev;
        }
        if (response.data && response.data.length > 0) {
          return String(response.data[0].id);
        }
        return '';
      });
    } catch {
      setVersions([]);
    }
  };

  const handleRollback = async () => {
    if (!selectedTable || !selectedVersionId) {
      setError('Выберите версию для отката');
      return;
    }

    if (!window.confirm(`Откатить таблицу к версии #${selectedVersionId}? Текущее состояние будет заменено.`)) {
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');
    try {
      const response = await tableService.rollbackTableToVersion(selectedTable, Number(selectedVersionId));
      setSuccess(response.data?.message || `Откат к версии #${selectedVersionId} выполнен`);
      setSelectedRowIds([]);
      await loadTableData(0);
      await loadVersions(selectedTable);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка отката версии');
    } finally {
      setLoading(false);
    }
  };

  const startEditRow = (row: any) => {
    setEditingRowId(Number(row.id));
    const values: Record<string, any> = {};
    Object.keys(row).forEach((key) => {
      if (key !== 'id') {
        values[key] = row[key] ?? '';
      }
    });
    setEditValues(values);
  };

  const cancelEdit = () => {
    setEditingRowId(null);
    setEditValues({});
  };

  const saveEditRow = async () => {
    if (!selectedTable || editingRowId === null) return;

    setLoading(true);
    setError('');
    setSuccess('');
    try {
      await tableService.updateRow(selectedTable, editingRowId, editValues);
      setEditingRowId(null);
      setEditValues({});
      await loadTableData(currentPage);
      await loadVersions(selectedTable);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка при сохранении строки');
    } finally {
      setLoading(false);
    }
  };

  const addRow = async () => {
    if (!selectedTable) return;

    const payload = Object.fromEntries(
      Object.entries(newRowValues).filter(([, value]) => String(value).trim() !== '')
    );

    if (Object.keys(payload).length === 0) {
      setError('Заполните хотя бы одно поле для новой строки');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');
    try {
      await tableService.createRow(selectedTable, payload);
      setNewRowValues({});
      await loadTableData(0);
      await loadVersions(selectedTable);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка при добавлении строки');
    } finally {
      setLoading(false);
    }
  };

  const deleteSelectedRows = async () => {
    if (!selectedTable || selectedRowIds.length === 0) return;
    if (!window.confirm(`Удалить выбранные строки: ${selectedRowIds.length} шт.?`)) return;

    setLoading(true);
    setError('');
    setSuccess('');
    try {
      await tableService.deleteRows(selectedTable, selectedRowIds);
      setSelectedRowIds([]);
      await loadTableData(currentPage);
      await loadVersions(selectedTable);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка при удалении строк');
    } finally {
      setLoading(false);
    }
  };

  const toggleRowSelection = (rowId: number) => {
    setSelectedRowIds((prev) =>
      prev.includes(rowId) ? prev.filter((id) => id !== rowId) : [...prev, rowId]
    );
  };

  const handleExport = async () => {
    if (!selectedTable) return;

    try {
      const response = await tableService.exportTableCsv(selectedTable);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${selectedTable}.csv`);
      document.body.appendChild(link);
      link.click();
      link.parentElement?.removeChild(link);
    } catch (err) {
      setError('Ошибка при экспорте файла');
    }
  };

  const handleDeleteTable = async (tableName: string) => {
    if (!window.confirm(`Вы уверены, что хотите удалить таблицу "${tableName}"? Это действие необратимо.`)) {
      return;
    }

    setLoading(true);
    setError('');
    try {
      await tableService.deleteTable(tableName);
      setSelectedTable('');
      setTableData(null);
      onTablesChange();
      setError('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка при удалении таблицы');
    } finally {
      setLoading(false);
      setDeleteConfirm(null);
    }
  };

  const filteredData = tableData?.data.filter((row) =>
    Object.values(row).some((val) =>
      String(val).toLowerCase().includes(searchTerm.toLowerCase())
    )
  ) || [];

  const columns =
    tableData && tableData.data.length > 0
      ? Object.keys(tableData.data[0])
      : [];

  return (
    <div className="view-table-card">
      <h2>📋 Просмотр таблиц</h2>

      <div className="controls-section">
        <div className="select-group">
          <label htmlFor="table-select">Выберите таблицу:</label>
          <select
            id="table-select"
            value={selectedTable}
            onChange={(e: React.ChangeEvent<HTMLSelectElement>) => {
              setSelectedTable(e.target.value);
              setSearchTerm('');
            }}
          >
            <option value="">-- Выберите таблицу --</option>
            {tables.map((table) => (
              <option key={table} value={table}>
                {table}
              </option>
            ))}
          </select>
        </div>

        {selectedTable && (
          <div className="action-buttons">
            <button
              onClick={handleExport}
              disabled={loading || !tableData}
              className="btn btn-secondary"
              title="Экспортировать в CSV"
            >
              📥 Экспорт CSV
            </button>
            <button
              onClick={() => setDeleteConfirm(selectedTable)}
              disabled={loading}
              className="btn btn-danger"
              title="Удалить таблицу"
            >
              🗑️ Удалить таблицу
            </button>
          </div>
        )}
      </div>

      {selectedTable && (
        <div className="version-controls">
          <label htmlFor="version-select">Версия для отката:</label>
          <select
            id="version-select"
            value={selectedVersionId}
            onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setSelectedVersionId(e.target.value)}
            disabled={loading || versions.length === 0}
          >
            {versions.length === 0 && <option value="">Нет доступных версий</option>}
            {versions.map((version) => (
              <option key={version.id} value={String(version.id)}>
                #{version.id} • {version.action} • rows: {version.row_count} • {new Date(version.created_at).toLocaleString()}
              </option>
            ))}
          </select>
          <button
            className="btn btn-warning"
            onClick={handleRollback}
            disabled={loading || !selectedVersionId}
          >
            ⏪ Откатить версию
          </button>
        </div>
      )}

      {deleteConfirm && (
        <div className="confirm-dialog">
          <div className="confirm-content">
            <p>Вы уверены, что хотите удалить таблицу "{deleteConfirm}"?</p>
            <p className="warn-text">⚠️ Это действие необратимо!</p>
            <div className="confirm-buttons">
              <button
                onClick={() => handleDeleteTable(deleteConfirm)}
                className="btn btn-danger"
                disabled={loading}
              >
                Да, удалить
              </button>
              <button
                onClick={() => setDeleteConfirm(null)}
                className="btn btn-secondary"
                disabled={loading}
              >
                Отмена
              </button>
            </div>
          </div>
        </div>
      )}

      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}

      {selectedTable && tableData && (
        <div className="table-view-section">
          <div className="table-header">
            <h3>{selectedTable}</h3>
            <div className="table-stats">
              <span className="stat">📊 Всего строк: <strong>{tableData.total}</strong></span>
              <span className="stat">👁️ На странице: <strong>{filteredData.length}</strong></span>
            </div>
          </div>

          {tableData.total > 0 && (
            <div className="search-box">
              <input
                type="text"
                placeholder="🔍 Поиск в таблице..."
                value={searchTerm}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchTerm(e.target.value)}
                className="search-input"
              />
            </div>
          )}

          {tableData.total > 0 && (
            <div className="row-actions-toolbar">
              <button
                className="btn btn-danger btn-small"
                disabled={loading || selectedRowIds.length === 0}
                onClick={deleteSelectedRows}
              >
                🗑️ Удалить выбранные ({selectedRowIds.length})
              </button>
            </div>
          )}

          {loading ? (
            <div className="loading">Загрузка данных...</div>
          ) : tableData.total === 0 ? (
            <div className="empty-message">Таблица пуста</div>
          ) : (
            <>
              <div className="table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th style={{ width: '40px' }}></th>
                      {columns.map((col) => (
                        <th key={col}>{col}</th>
                      ))}
                      <th style={{ width: '180px' }}>Действия</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr className="new-row">
                      <td>＋</td>
                      {columns.map((col) => (
                        <td key={`new-${col}`}>
                          {col === 'id' ? (
                            <span className="new-row-hint">auto</span>
                          ) : (
                            <input
                              className="cell-input"
                              value={newRowValues[col] ?? ''}
                              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                                setNewRowValues((prev) => ({ ...prev, [col]: e.target.value }))
                              }
                              placeholder={col}
                            />
                          )}
                        </td>
                      ))}
                      <td>
                        <button className="btn btn-secondary btn-small" onClick={addRow} disabled={loading}>
                          Добавить
                        </button>
                      </td>
                    </tr>
                    {filteredData.map((row, idx) => (
                      <tr key={idx} className={idx % 2 === 0 ? 'even' : 'odd'}>
                        <td>
                          <input
                            type="checkbox"
                            checked={selectedRowIds.includes(Number(row.id))}
                            onChange={() => toggleRowSelection(Number(row.id))}
                          />
                        </td>
                        {columns.map((col) => (
                          <td key={`${idx}-${col}`}>
                            {editingRowId === Number(row.id) && col !== 'id' ? (
                              <input
                                className="cell-input"
                                value={editValues[col] ?? ''}
                                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                                  setEditValues((prev) => ({ ...prev, [col]: e.target.value }))
                                }
                              />
                            ) : (
                              row[col] !== null && row[col] !== undefined
                                ? String(row[col]).substring(0, 100)
                                : '—'
                            )}
                          </td>
                        ))}
                        <td>
                          {editingRowId === Number(row.id) ? (
                            <div className="inline-actions">
                              <button className="btn btn-small btn-secondary" onClick={saveEditRow} disabled={loading}>
                                Сохранить
                              </button>
                              <button className="btn btn-small" onClick={cancelEdit} disabled={loading}>
                                Отмена
                              </button>
                            </div>
                          ) : (
                            <button className="btn btn-small" onClick={() => startEditRow(row)} disabled={loading}>
                              ✏️ Изменить
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="pagination">
                <button
                  onClick={() => loadTableData(currentPage - 1)}
                  disabled={currentPage === 0 || loading}
                  className="btn btn-sm"
                >
                  ← Назад
                </button>
                <span className="page-info">
                  Страница {currentPage + 1} из {Math.ceil(tableData.total / pageSize)}
                </span>
                <button
                  onClick={() => loadTableData(currentPage + 1)}
                  disabled={(currentPage + 1) * pageSize >= tableData.total || loading}
                  className="btn btn-sm"
                >
                  Вперёд →
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default ViewTable;
