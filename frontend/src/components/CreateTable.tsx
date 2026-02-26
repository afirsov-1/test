import React, { useState } from 'react';
import { tableService } from '../services/api';
import '../styles/createTable.css';

interface Column {
  name: string;
  type: string;
  nullable: boolean;
  unique: boolean;
  max_length?: number;
}

interface CreateTableProps {
  onTableCreated: () => void;
}

const CreateTable: React.FC<CreateTableProps> = ({ onTableCreated }) => {
  const [tableName, setTableName] = useState('');
  const [columns, setColumns] = useState<Column[]>([
    { name: '', type: 'varchar', nullable: true, unique: false, max_length: 255 },
  ]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const columnTypes = ['varchar', 'integer', 'decimal', 'date', 'timestamp', 'boolean', 'text'];

  const handleColumnChange = (index: number, field: string, value: any) => {
    const newColumns = [...columns];
    newColumns[index] = { ...newColumns[index], [field]: value };
    setColumns(newColumns);
  };

  const addColumn = () => {
    setColumns([
      ...columns,
      { name: '', type: 'varchar', nullable: true, unique: false, max_length: 255 },
    ]);
  };

  const removeColumn = (index: number) => {
    setColumns(columns.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!tableName.trim()) {
      setError('Table name is required');
      return;
    }

    const validColumns = columns.filter((col) => col.name.trim());
    if (validColumns.length === 0) {
      setError('At least one column is required');
      return;
    }

    setLoading(true);

    try {
      await tableService.createTable(tableName, validColumns);
      setSuccess(`Table "${tableName}" created successfully`);
      setTableName('');
      setColumns([{ name: '', type: 'varchar', nullable: true, unique: false, max_length: 255 }]);
      onTableCreated();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create table');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="create-table-card">
      <h2>Создать таблицу</h2>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="table-name">Название таблицы</label>
          <input
            id="table-name"
            type="text"
            value={tableName}
            onChange={(e) => setTableName(e.target.value)}
            placeholder="имя_таблицы"
            required
          />
        </div>

        <div className="columns-section">
          <h3>Колонки</h3>
          {columns.map((column, index) => (
            <div key={index} className="column-row">
              <input
                type="text"
                value={column.name}
                onChange={(e) => handleColumnChange(index, 'name', e.target.value)}
                placeholder="Название колонки"
                className="column-input"
              />

              <select
                value={column.type}
                onChange={(e) => handleColumnChange(index, 'type', e.target.value)}
                className="column-select"
              >
                {columnTypes.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>

              {column.type === 'varchar' && (
                <input
                  type="number"
                  value={column.max_length}
                  onChange={(e) => handleColumnChange(index, 'max_length', parseInt(e.target.value))}
                  placeholder="Max length"
                  className="column-input small"
                  min="1"
                  max="1000"
                />
              )}

              <label className="checkbox">
                <input
                  type="checkbox"
                  checked={column.nullable}
                  onChange={(e) => handleColumnChange(index, 'nullable', e.target.checked)}
                />
                Nullable
              </label>

              <label className="checkbox">
                <input
                  type="checkbox"
                  checked={column.unique}
                  onChange={(e) => handleColumnChange(index, 'unique', e.target.checked)}
                />
                Unique
              </label>

              <button
                type="button"
                onClick={() => removeColumn(index)}
                className="btn btn-danger btn-small"
                disabled={columns.length === 1}
              >
                Удалить
              </button>
            </div>
          ))}

          <button type="button" onClick={addColumn} className="btn btn-secondary">
            + Добавить колонку
          </button>
        </div>

        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}

        <button type="submit" disabled={loading} className="btn btn-primary">
          {loading ? 'Создание...' : 'Создать таблицу'}
        </button>
      </form>
    </div>
  );
};

export default CreateTable;
