import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('access_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authService = {
  register: (username: string, email: string, password: string) =>
    api.post('/auth/register', { username, email, password }),
  
  login: (username: string, password: string) =>
    api.post('/auth/login', { username, password }),
  
  me: () =>
    api.get('/auth/me'),

  verify: (token: string) =>
    api.post('/auth/verify', { token }),
};

export const tableService = {
  createTable: (tableName: string, columns: any[]) =>
    api.post('/tables/create', { table_name: tableName, columns }),
  
  listTables: () =>
    api.get('/tables/list'),
  
  getTableSchema: (tableName: string) =>
    api.get(`/tables/${tableName}`),
  
  getTableData: (tableName: string, limit: number = 100, offset: number = 0) =>
    api.get(`/tables/${tableName}/data`, { params: { limit, offset } }),

  getTableVersions: (tableName: string, limit: number = 20) =>
    api.get(`/tables/${tableName}/versions`, { params: { limit } }),

  rollbackTableToVersion: (tableName: string, versionId: number) =>
    api.post(`/tables/${tableName}/rollback/${versionId}`),

  createRow: (tableName: string, values: Record<string, any>) =>
    api.post(`/tables/${tableName}/rows`, { values }),

  updateRow: (tableName: string, rowId: number, values: Record<string, any>) =>
    api.put(`/tables/${tableName}/rows/${rowId}`, { values }),

  deleteRows: (tableName: string, rowIds: number[]) =>
    api.delete(`/tables/${tableName}/rows`, { data: { row_ids: rowIds } }),
  
  deleteTable: (tableName: string) =>
    api.delete(`/tables/${tableName}`),
  
  exportTableCsv: (tableName: string) =>
    api.get(`/tables/${tableName}/export`, { responseType: 'blob' }),
  
  previewCSV: (
    file: File,
    options?: { delimiter?: string; encoding?: string; preview_limit?: number }
  ) => {
    const formData = new FormData();
    formData.append('file', file);
    if (options) {
      formData.append('request', JSON.stringify(options));
    }

    return api.post('/tables/import-csv/preview', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  importCSV: (
    file: File,
    tableName: string,
    columnsMapping: Record<string, string>,
    options?: { delimiter?: string; encoding?: string; edited_preview_rows?: Array<Record<string, any>> }
  ) => {
    const formData = new FormData();
    formData.append('file', file);
    const requestPayload: Record<string, any> = {
      table_name: tableName,
      columns_mapping: columnsMapping,
    };
    if (options?.delimiter) {
      requestPayload.delimiter = options.delimiter;
    }
    if (options?.encoding) {
      requestPayload.encoding = options.encoding;
    }
    if (options?.edited_preview_rows && options.edited_preview_rows.length > 0) {
      requestPayload.edited_preview_rows = options.edited_preview_rows;
    }
    formData.append('request', JSON.stringify({
      ...requestPayload,
    }));
    
    return api.post('/tables/import-csv', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  startImportJob: (
    file: File,
    tableName: string,
    columnsMapping: Record<string, string>,
    options?: { delimiter?: string; encoding?: string; edited_preview_rows?: Array<Record<string, any>> }
  ) => {
    const formData = new FormData();
    formData.append('file', file);

    const requestPayload: Record<string, any> = {
      table_name: tableName,
      columns_mapping: columnsMapping,
    };
    if (options?.delimiter) {
      requestPayload.delimiter = options.delimiter;
    }
    if (options?.encoding) {
      requestPayload.encoding = options.encoding;
    }
    if (options?.edited_preview_rows && options.edited_preview_rows.length > 0) {
      requestPayload.edited_preview_rows = options.edited_preview_rows;
    }
    formData.append('request', JSON.stringify(requestPayload));

    return api.post('/tables/import-csv/async', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  getImportJobStatus: (jobId: string) =>
    api.get(`/tables/import-csv/jobs/${jobId}`),
  
  getImportHistory: () =>
    api.get('/tables/history/list'),
};

export interface PermissionPayload {
  username: string;
  table_name: string;
  can_read: boolean;
  can_write: boolean;
  can_alter: boolean;
  can_delete: boolean;
  is_owner: boolean;
}

export interface AuditLogItem {
  id: number;
  user_id: number;
  username: string;
  action: string;
  entity_type: string;
  entity_name?: string | null;
  status: string;
  details?: Record<string, any> | null;
  created_at: string;
}

export interface ConnectionItem {
  id: number;
  name: string;
  db_type: string;
  is_shared: boolean;
  is_active: boolean;
  created_by: number;
  created_at: string;
  updated_at: string;
}

export const adminService = {
  listUsers: () =>
    api.get('/admin/users'),

  getTablePermissions: (tableName: string) =>
    api.get(`/admin/permissions/${tableName}`),

  grantPermission: (payload: PermissionPayload) =>
    api.post('/admin/permissions/grant', payload),

  revokePermission: (username: string, tableName: string) =>
    api.post('/admin/permissions/revoke', {
      username,
      table_name: tableName,
      can_read: false,
      can_write: false,
      can_alter: false,
      can_delete: false,
      is_owner: false,
    }),

  blockPermission: (username: string, tableName: string, blockedUntil?: string) =>
    api.post('/admin/permissions/block', {
      username,
      table_name: tableName,
      blocked_until: blockedUntil || null,
    }),

  unblockPermission: (username: string, tableName: string) =>
    api.post('/admin/permissions/unblock', {
      username,
      table_name: tableName,
    }),

  getAuditLogs: (params?: { limit?: number; username?: string; action?: string; table_name?: string }) =>
    api.get('/admin/audit', { params }),
};

export const connectionService = {
  listConnections: () =>
    api.get('/connections/list'),

  createConnection: (payload: { name: string; db_type: string; connection_url: string; is_shared: boolean }) =>
    api.post('/connections/create', payload),

  setActiveConnection: (connectionId: number) =>
    api.post(`/connections/set-active/${connectionId}`),

  clearActiveConnection: () =>
    api.post('/connections/clear-active'),

  testConnection: (connectionId: number) =>
    api.post(`/connections/test/${connectionId}`),
};

export default api;
