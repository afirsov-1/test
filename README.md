# Export CSV to DB

Приложение для импорта CSV файлов в базу данных PostgreSQL с веб-интерфейсом и административными возможностями.

## Функциональность

✅ **Аутентификация** - Вход по логину и паролю  
✅ **Загрузка CSV** - Импорт CSV файлов в таблицы БД  
✅ **Создание таблиц** - Интерфейс для создания таблиц без SQL-запросов  
✅ **Валидация данных** - Проверка данных при импорте с подробными ошибками  
✅ **История операций** - Отслеживание всех импортов  

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

### 4. Запустите Backend

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend будет доступен на `http://localhost:8000`
API документация: `http://localhost:8000/docs`

### 5. Установите зависимости Frontend

```bash
cd frontend
npm install
```

### 6. Запустите Frontend

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
2. Выберите таблицу из списка
3. Загрузите CSV файл
4. Сопоставьте колонки CSV с колонками таблицы
5. Нажмите "Импортировать"
6. Если есть ошибки валидации, они будут показаны с предложением решения

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

### Таблицы
- `POST /api/tables/create` - Создать таблицу
- `GET /api/tables/list` - Список таблиц
- `GET /api/tables/{table_name}` - Информация о таблице
- `POST /api/tables/import-csv` - Импорт CSV
- `GET /api/tables/history/list` - История импортов

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
