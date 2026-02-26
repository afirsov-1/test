import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authService = {
  register: (username: string, email: string, password: string) =>
    api.post('/auth/register', { username, email, password }),
  
  login: (username: string, password: string) =>
    api.post('/auth/login', { username, password }),
  
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
  
  importCSV: (file: File, tableName: string, columnsMapping: Record<string, string>) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('request', JSON.stringify({
      table_name: tableName,
      columns_mapping: columnsMapping,
    }));
    
    return api.post('/tables/import-csv', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  
  getImportHistory: () =>
    api.get('/tables/history/list'),
};

export default api;
