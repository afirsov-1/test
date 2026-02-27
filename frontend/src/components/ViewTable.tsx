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

const ViewTable: React.FC<ViewTableProps> = ({ tables, onTablesChange }): JSX.Element => {
  const [selectedTable, setSelectedTable] = useState('');
  const [tableData, setTableData] = useState<TableData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [currentPage, setCurrentPage] = useState(0);
  const [pageSize] = useState(10);
  const [searchTerm, setSearchTerm] = useState('');
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  useEffect(() => {
    if (selectedTable) {
      loadTableData(0);
    }
  }, [selectedTable]);

  const loadTableData = async (page: number) => {
    if (!selectedTable) return;

    setLoading(true);
    setError('');
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
                      {columns.map((col) => (
                        <th key={col}>{col}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {filteredData.map((row, idx) => (
                      <tr key={idx} className={idx % 2 === 0 ? 'even' : 'odd'}>
                        {columns.map((col) => (
                          <td key={`${idx}-${col}`}>
                            {row[col] !== null && row[col] !== undefined
                              ? String(row[col]).substring(0, 100)
                              : '—'}
                          </td>
                        ))}
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
