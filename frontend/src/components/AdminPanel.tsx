import { useEffect, useMemo, useState } from 'react';
import { adminService, AuditLogItem, connectionService, ConnectionItem, PermissionPayload } from '../services/api';
import '../styles/adminPanel.css';

interface AdminPanelProps {
  tables: string[];
  onConnectionsChanged: () => void;
}

interface UserSummary {
  id: number;
  username: string;
  email: string;
  role: string;
  is_active: number;
}

interface PermissionRow {
  username: string;
  table_name: string;
  can_read: boolean;
  can_write: boolean;
  can_alter: boolean;
  can_delete: boolean;
  is_owner: boolean;
  blocked_until?: string | null;
}

const emptyPermissionForm: PermissionPayload = {
  username: '',
  table_name: '',
  can_read: true,
  can_write: false,
  can_alter: false,
  can_delete: false,
  is_owner: false,
};

const AdminPanel: React.FC<AdminPanelProps> = ({ tables, onConnectionsChanged }): JSX.Element => {
  const [users, setUsers] = useState<UserSummary[]>([]);
  const [selectedTable, setSelectedTable] = useState('');
  const [permissions, setPermissions] = useState<PermissionRow[]>([]);
  const [form, setForm] = useState<PermissionPayload>(emptyPermissionForm);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([]);
  const [auditUsername, setAuditUsername] = useState('');
  const [auditAction, setAuditAction] = useState('');
  const [connections, setConnections] = useState<ConnectionItem[]>([]);
  const [newConnectionName, setNewConnectionName] = useState('');
  const [newConnectionUrl, setNewConnectionUrl] = useState('');
  const [newConnectionShared, setNewConnectionShared] = useState(false);

  const operators = useMemo(() => users.filter((user) => user.role !== 'admin'), [users]);

  useEffect(() => {
    loadUsers();
    loadAuditLogs();
    loadConnections();
  }, []);

  useEffect(() => {
    if (selectedTable) {
      loadPermissions(selectedTable);
      setForm((prev) => ({ ...prev, table_name: selectedTable }));
      loadAuditLogs(selectedTable);
    }
  }, [selectedTable]);

  const loadUsers = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await adminService.listUsers();
      setUsers(response.data.value || response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Не удалось загрузить пользователей');
    } finally {
      setLoading(false);
    }
  };

  const loadPermissions = async (tableName: string) => {
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      const response = await adminService.getTablePermissions(tableName);
      setPermissions(response.data);
    } catch (err: any) {
      setPermissions([]);
      setError(err.response?.data?.detail || 'Не удалось загрузить права таблицы');
    } finally {
      setLoading(false);
    }
  };

  const loadAuditLogs = async (tableName?: string) => {
    try {
      const response = await adminService.getAuditLogs({
        limit: 100,
        username: auditUsername || undefined,
        action: auditAction || undefined,
        table_name: tableName || selectedTable || undefined,
      });
      setAuditLogs(response.data || []);
    } catch (err: any) {
      setAuditLogs([]);
      setError(err.response?.data?.detail || 'Не удалось загрузить аудит-логи');
    }
  };

  const loadConnections = async () => {
    try {
      const response = await connectionService.listConnections();
      setConnections(response.data || []);
    } catch (err: any) {
      setConnections([]);
      setError(err.response?.data?.detail || 'Не удалось загрузить подключения');
    }
  };

  const handleCreateConnection = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newConnectionName || !newConnectionUrl) {
      setError('Укажите имя и connection URL');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');
    try {
      await connectionService.createConnection({
        name: newConnectionName,
        db_type: 'postgresql',
        connection_url: newConnectionUrl,
        is_shared: newConnectionShared,
      });

      setSuccess('Подключение сохранено');
      setNewConnectionName('');
      setNewConnectionUrl('');
      setNewConnectionShared(false);
      await loadConnections();
      onConnectionsChanged();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Не удалось создать подключение');
    } finally {
      setLoading(false);
    }
  };

  const handleSetActiveConnection = async (connectionId: number) => {
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      await connectionService.setActiveConnection(connectionId);
      setSuccess(`Активное подключение: #${connectionId}`);
      await loadConnections();
      onConnectionsChanged();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Не удалось установить активное подключение');
    } finally {
      setLoading(false);
    }
  };

  const handleClearActiveConnection = async () => {
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      await connectionService.clearActiveConnection();
      setSuccess('Активное подключение сброшено на primary');
      await loadConnections();
      onConnectionsChanged();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Не удалось сбросить активное подключение');
    } finally {
      setLoading(false);
    }
  };

  const handleTestConnection = async (connectionId: number) => {
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      await connectionService.testConnection(connectionId);
      setSuccess(`Подключение #${connectionId} успешно проверено`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Проверка подключения не удалась');
    } finally {
      setLoading(false);
    }
  };

  const handleGrantOrUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.username || !form.table_name) {
      setError('Выберите пользователя и таблицу');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');
    try {
      await adminService.grantPermission(form);
      setSuccess('Права успешно обновлены');
      await loadPermissions(form.table_name);
      await loadAuditLogs(form.table_name);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Не удалось обновить права');
    } finally {
      setLoading(false);
    }
  };

  const handleRevoke = async (username: string) => {
    if (!selectedTable) return;

    setLoading(true);
    setError('');
    setSuccess('');
    try {
      await adminService.revokePermission(username, selectedTable);
      setSuccess(`Права пользователя ${username} отозваны`);
      await loadPermissions(selectedTable);
      await loadAuditLogs(selectedTable);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Не удалось отозвать права');
    } finally {
      setLoading(false);
    }
  };

  const handleBlockToggle = async (permission: PermissionRow) => {
    if (!selectedTable) return;

    setLoading(true);
    setError('');
    setSuccess('');
    try {
      if (permission.blocked_until) {
        await adminService.unblockPermission(permission.username, selectedTable);
        setSuccess(`Доступ пользователя ${permission.username} восстановлен`);
      } else {
        await adminService.blockPermission(permission.username, selectedTable);
        setSuccess(`Доступ пользователя ${permission.username} временно заблокирован`);
      }
      await loadPermissions(selectedTable);
      await loadAuditLogs(selectedTable);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Не удалось изменить блокировку доступа');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="admin-panel-card">
      <h2>🛡️ Администрирование прав доступа</h2>

      <div className="admin-grid">
        <section className="admin-section">
          <h3>1) Выбор таблицы</h3>
          <select
            value={selectedTable}
            onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setSelectedTable(e.target.value)}
            disabled={loading}
          >
            <option value="">-- Выберите таблицу --</option>
            {tables.map((table) => (
              <option key={table} value={table}>
                {table}
              </option>
            ))}
          </select>

          <h3>2) Назначить/обновить права</h3>
          <form onSubmit={handleGrantOrUpdate} className="permission-form">
            <div className="form-group">
              <label htmlFor="user-select">Пользователь</label>
              <select
                id="user-select"
                value={form.username}
                onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
                  setForm((prev) => ({ ...prev, username: e.target.value }))
                }
                disabled={loading}
              >
                <option value="">-- Выберите пользователя --</option>
                {operators.map((user) => (
                  <option key={user.id} value={user.username}>
                    {user.username} ({user.email})
                  </option>
                ))}
              </select>
            </div>

            <div className="checkbox-grid">
              <label className="checkbox">
                <input
                  type="checkbox"
                  checked={form.can_read}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setForm((prev) => ({ ...prev, can_read: e.target.checked }))
                  }
                />
                Чтение
              </label>
              <label className="checkbox">
                <input
                  type="checkbox"
                  checked={form.can_write}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setForm((prev) => ({ ...prev, can_write: e.target.checked }))
                  }
                />
                Запись
              </label>
              <label className="checkbox">
                <input
                  type="checkbox"
                  checked={form.can_alter}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setForm((prev) => ({ ...prev, can_alter: e.target.checked }))
                  }
                />
                Изменение структуры
              </label>
              <label className="checkbox">
                <input
                  type="checkbox"
                  checked={form.can_delete}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setForm((prev) => ({ ...prev, can_delete: e.target.checked }))
                  }
                />
                Удаление таблицы
              </label>
              <label className="checkbox owner">
                <input
                  type="checkbox"
                  checked={form.is_owner}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setForm((prev) => ({ ...prev, is_owner: e.target.checked }))
                  }
                />
                Сделать владельцем
              </label>
            </div>

            <button type="submit" className="btn btn-primary" disabled={loading || !selectedTable}>
              Сохранить права
            </button>
          </form>
        </section>

        <section className="admin-section">
          <h3>3) Текущие права по таблице</h3>
          {selectedTable ? (
            <>
              <p className="selected-table">Таблица: <strong>{selectedTable}</strong></p>
              <div className="permissions-table-wrapper">
                <table className="permissions-table">
                  <thead>
                    <tr>
                      <th>Пользователь</th>
                      <th>R</th>
                      <th>W</th>
                      <th>A</th>
                      <th>D</th>
                      <th>Owner</th>
                      <th>Статус</th>
                      <th>Действия</th>
                    </tr>
                  </thead>
                  <tbody>
                    {permissions.length === 0 ? (
                      <tr>
                        <td colSpan={8} className="empty-cell">Права пока не назначены</td>
                      </tr>
                    ) : (
                      permissions.map((permission) => (
                        <tr key={`${permission.username}-${permission.table_name}`}>
                          <td>{permission.username}</td>
                          <td>{permission.can_read ? '✓' : '—'}</td>
                          <td>{permission.can_write ? '✓' : '—'}</td>
                          <td>{permission.can_alter ? '✓' : '—'}</td>
                          <td>{permission.can_delete ? '✓' : '—'}</td>
                          <td>{permission.is_owner ? '✓' : '—'}</td>
                          <td>{permission.blocked_until ? 'Заблокирован' : 'Активен'}</td>
                          <td>
                            <div className="row-actions">
                              <button
                                className="btn btn-small btn-secondary"
                                onClick={() => handleBlockToggle(permission)}
                                disabled={loading}
                              >
                                {permission.blocked_until ? 'Разблокировать' : 'Блокировать'}
                              </button>
                              <button
                                className="btn btn-small btn-danger"
                                onClick={() => handleRevoke(permission.username)}
                                disabled={loading}
                              >
                                Отозвать
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <p className="empty-message">Выберите таблицу слева, чтобы управлять правами</p>
          )}
        </section>
      </div>

      <section className="admin-section audit-section">
        <h3>5) Подключения баз данных</h3>

        <form onSubmit={handleCreateConnection} className="connection-form">
          <input
            placeholder="Имя подключения"
            value={newConnectionName}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewConnectionName(e.target.value)}
            disabled={loading}
          />
          <input
            placeholder="postgresql://user:password@host:5432/db"
            value={newConnectionUrl}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewConnectionUrl(e.target.value)}
            disabled={loading}
          />
          <label className="checkbox">
            <input
              type="checkbox"
              checked={newConnectionShared}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewConnectionShared(e.target.checked)}
              disabled={loading}
            />
            Shared
          </label>
          <button className="btn btn-primary" type="submit" disabled={loading}>
            Добавить подключение
          </button>
        </form>

        <div className="permissions-table-wrapper">
          <table className="permissions-table audit-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Имя</th>
                <th>Тип</th>
                <th>Shared</th>
                <th>Действия</th>
              </tr>
            </thead>
            <tbody>
              {connections.length === 0 ? (
                <tr>
                  <td colSpan={5} className="empty-cell">Подключения не настроены</td>
                </tr>
              ) : (
                connections.map((connection) => (
                  <tr key={`connection-${connection.id}`}>
                    <td>{connection.id}</td>
                    <td>{connection.name}</td>
                    <td>{connection.db_type}</td>
                    <td>{connection.is_shared ? '✓' : '—'}</td>
                    <td>
                      <div className="row-actions">
                        <button className="btn btn-small btn-secondary" onClick={() => handleTestConnection(connection.id)} disabled={loading}>
                          Test
                        </button>
                        <button className="btn btn-small btn-primary" onClick={() => handleSetActiveConnection(connection.id)} disabled={loading}>
                          Set active
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <button className="btn btn-secondary" onClick={handleClearActiveConnection} disabled={loading}>
          Сбросить active connection
        </button>
      </section>

      <section className="admin-section audit-section">
        <h3>4) Аудит действий</h3>
        <div className="audit-controls">
          <select
            value={auditUsername}
            onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setAuditUsername(e.target.value)}
            disabled={loading}
          >
            <option value="">Все пользователи</option>
            {users.map((user) => (
              <option key={`audit-user-${user.id}`} value={user.username}>
                {user.username}
              </option>
            ))}
          </select>

          <input
            placeholder="Фильтр action (например row_update)"
            value={auditAction}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setAuditAction(e.target.value)}
            disabled={loading}
          />

          <button
            className="btn btn-secondary"
            onClick={() => loadAuditLogs()}
            disabled={loading}
          >
            Обновить логи
          </button>
        </div>

        <div className="permissions-table-wrapper">
          <table className="permissions-table audit-table">
            <thead>
              <tr>
                <th>Время</th>
                <th>Пользователь</th>
                <th>Action</th>
                <th>Сущность</th>
                <th>Статус</th>
                <th>Детали</th>
              </tr>
            </thead>
            <tbody>
              {auditLogs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="empty-cell">Логи не найдены</td>
                </tr>
              ) : (
                auditLogs.map((log) => (
                  <tr key={`audit-${log.id}`}>
                    <td>{new Date(log.created_at).toLocaleString()}</td>
                    <td>{log.username}</td>
                    <td>{log.action}</td>
                    <td>{log.entity_type}:{' '}{log.entity_name || '—'}</td>
                    <td>{log.status}</td>
                    <td className="audit-details">{log.details ? JSON.stringify(log.details) : '—'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}
    </div>
  );
};

export default AdminPanel;
