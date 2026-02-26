# Структура проекта Export CSV to DB

```
export-csv-to-db/
│
├── backend/                          # FastAPI приложение
│   ├── app/
│   │   ├── models/
│   │   │   └── __init__.py          # SQLAlchemy модели (User, ImportHistory, TableSchema)
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py              # Routes: register, login, verify
│   │   │   └── tables.py            # Routes: create table, import CSV, get tables
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── schemas.py           # Pydantic models для валидации
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py              # JWT токены, хэширование паролей
│   │   │   ├── csv_handler.py       # Парсинг и валидация CSV
│   │   │   └── db_manager.py        # Управление таблицами БД
│   │   ├── __init__.py
│   │   ├── config.py                # Настройки приложения
│   │   └── main.py                  # FastAPI app и routes
│   ├── requirements.txt             # Python зависимости
│   ├── .env.example                 # Пример переменных окружения
│   └── [Dockerfile.backend]         # Docker конфиг для backend
│
├── frontend/                         # React приложение
│   ├── src/
│   │   ├── components/
│   │   │   ├── Login.tsx            # Компонент логина/регистрации
│   │   │   ├── CreateTable.tsx      # Компонент создания таблиц
│   │   │   └── CSVImport.tsx        # Компонент импорта CSV
│   │   ├── services/
│   │   │   └── api.ts              # HTTP клиент для API
│   │   ├── styles/
│   │   │   ├── index.css           # Глобальные стили
│   │   │   ├── app.css             # Стили приложения
│   │   │   ├── auth.css            # Стили авторизации
│   │   │   ├── createTable.css    # Стили создания таблиц
│   │   │   ├── csvImport.css       # Стили импорта CSV
│   │   │   └── tables.css          # Стили списка таблиц
│   │   ├── App.tsx                 # Главный компонент
│   │   └── main.tsx                # Entry point
│   ├── index.html                  # HTML файл
│   ├── package.json                # Node зависимости
│   ├── tsconfig.json               # TypeScript конфиг
│   ├── tsconfig.node.json          # TypeScript конфиг для Vite
│   ├── vite.config.ts              # Vite конфиг
│   ├── .eslintrc.cjs               # ESLint конфиг
│   ├── .prettierrc.json            # Prettier конфиг
│   ├── .prettierignore             # Prettier ignore
│   ├── .env.example                # Пример переменных окружения
│   └── [Dockerfile.frontend]       # Docker конфиг для frontend
│
├── examples/                        # Примеры CSV файлов
│   ├── users_example.csv           # Пример таблицы users
│   └── products_example.csv        # Пример таблицы products
│
├── docker-compose.yml              # Docker Compose для PostgreSQL
├── Dockerfile.backend              # Docker для backend
├── Dockerfile.frontend             # Docker для frontend
├── setup.bat                       # Windows скрипт установки
├── setup.sh                        # Unix скрипт установки
├── .gitignore                      # Git ignore
├── README.md                       # Полная документация
├── QUICKSTART.md                   # Быстрый старт
└── PROJECT_STRUCTURE.md            # Структура проекта (этот файл)
```

## Компоненты и их функционал

### Backend (FastAPI)

#### Models
- **User** - Пользователь (username, email, hashed_password)
- **ImportHistory** - История импортов CSV
- **TableSchema** - Метаданные о созданных таблицах

#### Routes
- **/api/auth/register** - Регистрация пользователя
- **/api/auth/login** - Вход в систему
- **/api/auth/verify** - Проверка JWT токена
- **/api/tables/create** - Создание таблицы
- **/api/tables/list** - Список всех таблиц
- **/api/tables/{table_name}** - Информация о таблице
- **/api/tables/import-csv** - Импорт CSV файла
- **/api/tables/history/list** - История импортов

#### Utilities
- **auth.py** - JWT создание/верификация, хэширование паролей bcrypt
- **csv_handler.py** - Парсинг CSV, валидация данных
- **db_manager.py** - Создание/удаление таблиц, работа с данными

### Frontend (React + TypeScript)

#### Components
- **Login** - Авторизация (двойная вкладка: вход/регистрация)
- **CreateTable** - Интерфейс для создания таблиц
- **CSVImport** - Загрузка CSV и импорт datos

#### Services
- **api.ts** - HTTP клиент с перехватчиком для токенов

#### Pages
- Главная страница с табами: Import, Create Table, Tables List

## Процесс импорта CSV

1. **Загрузка файла** - пользователь выбирает CSV файл
2. **Парсинг** - чтение заголовков и данных
3. **Сопоставление колонок** - выбор соответствия CSV → DB
4. **Валидация** - проверка типов, обязательных полей
5. **Импорт** - вставка валидных данных в БД
6. **История** - запись в историю успешный/неудачных импортов

## Валидация данных

Типы:
- `varchar` - строки (макс длина 255 по умолчанию)
- `integer` - целые числа
- `decimal` - дробные числа
- `date` - даты в формате YYYY-MM-DD
- `timestamp` - временные метки
- `boolean` - true/false
- `text` - длинные строки

Валидация:
- Проверка типов значений
- Проверка обязательных полей
- Проверка уникальности (если указано)
- Подробные сообщения об ошибках с предложениями решений

## Аутентификация

- JWT токены с истечением (30 минут по умолчанию)
- Хэширование паролей bcrypt
- Обязательна для всех операций кроме регистрации/логина

## Развертывание

### Development
- Backend: `uvicorn app.main:app --reload`
- Frontend: `npm run dev`
- Database: `docker-compose up -d`

### Production
- Docker контейнеры для backend и frontend
- Nginx для проксирования
- Environment переменные для конфигурации
