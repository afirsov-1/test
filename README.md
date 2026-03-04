# Export CSV to DB

Приложение для импорта CSV файлов в PostgreSQL с веб-интерфейсом, RBAC, аудитом, версионированием и мульти-БД подключениями.

## Функциональность

✅ **Аутентификация и роли** - JWT, роли `admin`/`operator`  
✅ **RBAC на уровне таблиц** - чтение/запись/изменение/удаление + owner  
✅ **Мастер CSV импорта** - preview, маппинг, delimiter/encoding, редактируемый preview  
✅ **Асинхронный импорт** - фоновые job с прогрессом и статусом  
✅ **Версионирование и откат** - снимки таблиц перед изменениями + rollback  
✅ **CRUD строк** - inline edit, добавление, удаление выбранных строк  
✅ **Аудит действий** - журнал операций в админ-панели  
✅ **Мульти-БД слой** - сохранённые подключения, active connection per user  

## Технологический стек

- **Backend**: Python, FastAPI, SQLAlchemy
- **Frontend**: React, TypeScript, Vite
- **БД**: PostgreSQL
- **Аутентификация**: JWT токены

## Установка и запуск

### 1. Создайте файл .env в папке backend

```bash
cp backend/.env.example backend/.env
```

Отредактируйте `backend/.env`:
```
DATABASE_URL=postgresql://user:password@localhost:5432/csv_to_db
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 2. Запустите PostgreSQL (Docker)

```bash
docker-compose up -d
```

Это запустит PostgreSQL на порту 5432 с credentials:
- Username: `user`
- Password: `password`
- Database: `csv_to_db`

### 3. Установите зависимости Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# MacOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 4. Примените миграции

```bash
cd backend
alembic upgrade head
```

### 5. Запустите Backend

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend будет доступен на `http://localhost:8000`
API документация: `http://localhost:8000/docs`

### 6. Установите зависимости Frontend

```bash
cd frontend
npm install
```

### 7. Запустите Frontend

```bash
cd frontend
npm run dev
```

Frontend будет доступен на `http://localhost:5173`

## Использование

### Регистрация

1. Откройте приложение на `http://localhost:5173`
2. Нажмите на "Зарегистрироваться"
3. Введите username, email и пароль
4. Кликните "Регистрация"

### Создание таблицы

1. Войдите в приложение
2. Перейдите на вкладку "Создать таблицу"
3. Укажите название таблицы
4. Добавьте колонки:
   - **Название** - имя колонки
   - **Тип** - varchar, integer, decimal, date, timestamp, boolean, text
   - **Nullable** - может ли колонка быть пустой
   - **Unique** - должны ли значения быть уникальными
5. Нажмите "Создать таблицу"

### Импорт CSV

1. Перейдите на вкладку "Импорт CSV"
2. Выберите таблицу и CSV-файл
3. Настройте delimiter/encoding и получите preview
4. Выполните сопоставление колонок
5. При необходимости включите асинхронный импорт с прогрессом
6. Нажмите "Импортировать"

### Администрирование

- Управление правами по таблицам (grant/revoke/block/unblock)
- Просмотр audit-логов
- Управление подключениями БД (create/test/set active/clear active)

### Версии и откат

- Во вкладке "Просмотр данных" доступен список версий таблицы
- Можно откатиться к выбранному snapshot

## Структура проекта

```
.
├── backend/
│   ├── app/
│   │   ├── models/       # SQLAlchemy модели
│   │   ├── routes/       # API routes
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── utils/        # Утилиты для auth, csv, db
│   │   ├── config.py     # Конфигурация
│   │   └── main.py       # FastAPI приложение
│   ├── requirements.txt   # Зависимости Python
│   └── .env.example      # Пример переменных окружения
├── frontend/
│   ├── src/
│   │   ├── components/   # React компоненты
│   │   ├── services/     # API клиент
│   │   ├── styles/       # CSS файлы
│   │   ├── App.tsx       # Главный компонент
│   │   └── main.tsx      # Entry point
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml
└── README.md
```

## API Endpoints

### Аутентификация
- `POST /api/auth/register` - Регистрация пользователя
- `POST /api/auth/login` - Вход
- `POST /api/auth/verify` - Проверка токена
- `GET /api/auth/me` - Профиль текущего пользователя

### Таблицы
- `POST /api/tables/create` - Создать таблицу
- `GET /api/tables/list` - Список таблиц
- `GET /api/tables/{table_name}` - Информация о таблице
- `GET /api/tables/{table_name}/data` - Данные таблицы
- `POST /api/tables/{table_name}/rows` - Добавить строку
- `PUT /api/tables/{table_name}/rows/{row_id}` - Обновить строку
- `DELETE /api/tables/{table_name}/rows` - Удалить строки
- `POST /api/tables/import-csv` - Импорт CSV
- `POST /api/tables/import-csv/preview` - Preview CSV
- `POST /api/tables/import-csv/async` - Асинхронный импорт
- `GET /api/tables/import-csv/jobs/{job_id}` - Статус async job
- `GET /api/tables/history/list` - История импортов
- `GET /api/tables/{table_name}/versions` - Версии таблицы
- `POST /api/tables/{table_name}/rollback/{version_id}` - Откат версии

### Администрирование
- `GET /api/admin/users`
- `GET /api/admin/permissions/{table_name}`
- `POST /api/admin/permissions/grant`
- `POST /api/admin/permissions/revoke`
- `POST /api/admin/permissions/block`
- `POST /api/admin/permissions/unblock`
- `GET /api/admin/audit`

### Подключения
- `GET /api/connections/list`
- `POST /api/connections/create`
- `POST /api/connections/test/{connection_id}`
- `POST /api/connections/set-active/{connection_id}`
- `POST /api/connections/clear-active`

## Примеры CSV

### Valid CSV
```csv
id,name,email,age
1,John,john@example.com,30
2,Jane,jane@example.com,25
```

### Валидация колонок
- Все колонки обязательны (если они не nullable)
- Типы данных проверяются (integer - только числа, date - только YYYY-MM-DD)
- Уникальные колонки - не проверяются на уникальность при импорте

## Обработка ошибок

При ошибке валидации система предоставляет:
- Номер строки с ошибкой
- Описание ошибки
- Предложение по ее исправлению

Примеры:
- "Неверный тип integer: 'abc'" → "Убедитесь, что значение - число"
- "Дата должна быть в формате YYYY-MM-DD" → "Используйте формат 2023-01-31"

## Развертывание

### Production с Docker

Создайте `Dockerfile` для backend и frontend, затем используйте docker-compose для развертывания всей системы.

## Лицензия

MIT

## Поддержка

Для вопросов и проблем - создайте issue.
