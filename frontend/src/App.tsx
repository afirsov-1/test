import { useEffect, useState } from 'react';
import Login from './components/Login';
import CreateTable from './components/CreateTable';
import CSVImport from './components/CSVImport';
import ViewTable from './components/ViewTable';
import AdminPanel from './components/AdminPanel';
import { authService, tableService } from './services/api';
import './styles/app.css';
import './styles/tables.css';
import './styles/adminPanel.css';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentRole, setCurrentRole] = useState<string>('operator');
  const [activeConnectionId, setActiveConnectionId] = useState<number | null>(null);
  const [tables, setTables] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState('import');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      hydrateSession();
    }
  }, []);

  const hydrateSession = async () => {
    try {
      const profile = await authService.me();
      setCurrentRole(profile.data.role || 'operator');
      setActiveConnectionId(profile.data.active_connection_id ?? null);
      setIsAuthenticated(true);
      fetchTables();
    } catch (err) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('username');
      setIsAuthenticated(false);
      setCurrentRole('operator');
      setActiveConnectionId(null);
    }
  };

  const handleLoginSuccess = () => {
    hydrateSession();
  };

  const fetchTables = async () => {
    setLoading(true);
    try {
      const response = await tableService.listTables();
      setTables(response.data);
    } catch (err) {
      console.error('Failed to fetch tables:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTableCreated = () => {
    fetchTables();
    setActiveTab('import');
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('username');
    setIsAuthenticated(false);
    setCurrentRole('operator');
    setActiveConnectionId(null);
    setTables([]);
    setActiveTab('import');
  };

  if (!isAuthenticated) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <h1>Export CSV to DB</h1>
          <div className="header-actions">
            <span className="username">Пользователь: {localStorage.getItem('username')}</span>
            <span className="username">Подключение: {activeConnectionId ? `#${activeConnectionId}` : 'primary'}</span>
            <button onClick={handleLogout} className="btn btn-logout">
              Выход
            </button>
          </div>
        </div>
      </header>

      <div className="app-container">
        <nav className="app-nav">
          <ul>
            <li>
              <button
                className={`nav-button ${activeTab === 'view' ? 'active' : ''}`}
                onClick={() => {
                  setActiveTab('view');
                  fetchTables();
                }}
              >
                📊 Просмотр данных
              </button>
            </li>
            <li>
              <button
                className={`nav-button ${activeTab === 'import' ? 'active' : ''}`}
                onClick={() => setActiveTab('import')}
              >
                📥 Импорт CSV
              </button>
            </li>
            <li>
              <button
                className={`nav-button ${activeTab === 'create' ? 'active' : ''}`}
                onClick={() => setActiveTab('create')}
              >
                ➕ Создать таблицу
              </button>
            </li>
            <li>
              <button
                className={`nav-button ${activeTab === 'tables' ? 'active' : ''}`}
                onClick={() => {
                  setActiveTab('tables');
                  fetchTables();
                }}
              >
                📋 Таблицы ({tables.length})
              </button>
            </li>
            {currentRole === 'admin' && (
              <li>
                <button
                  className={`nav-button ${activeTab === 'admin' ? 'active' : ''}`}
                  onClick={() => {
                    setActiveTab('admin');
                    fetchTables();
                  }}
                >
                  🛡️ Администрирование
                </button>
              </li>
            )}
          </ul>
        </nav>

        <main className="app-content">
          {activeTab === 'view' && (
            <ViewTable tables={tables} onTablesChange={fetchTables} />
          )}

          {activeTab === 'import' && (
            <CSVImport tables={tables} />
          )}

          {activeTab === 'create' && (
            <CreateTable onTableCreated={handleTableCreated} />
          )}

          {activeTab === 'tables' && (
            <div className="tables-list-card">
              <h2>📋 Список таблиц базы данных</h2>
              {loading ? (
                <p>Загрузка таблиц...</p>
              ) : tables.length > 0 ? (
                <>
                  <p style={{ marginBottom: '1.5rem', color: '#7f8c8d' }}>
                    Всего таблиц: <strong>{tables.length}</strong>
                  </p>
                  <ul className="tables-list">
                    {tables.map((table) => (
                      <li key={table} className="table-item">
                        <span>📊</span> {table}
                      </li>
                    ))}
                  </ul>
                </>
              ) : (
                <p className="empty-message">
                  📭 Таблицы не найдены. Создайте новую таблицу на вкладке "Создать таблицу"
                </p>
              )}
            </div>
          )}

          {activeTab === 'admin' && currentRole === 'admin' && (
            <AdminPanel tables={tables} onConnectionsChanged={hydrateSession} />
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
