# Быстрый старт - Export CSV to DB

## Требования

- Python 3.11+
- Node.js 18+
- Docker и Docker Compose
- PostgreSQL (через Docker)

## Шаг 1: Подготовка окружения

### Windows
```bash
setup.bat
```

### MacOS/Linux
```bash
chmod +x setup.sh
./setup.sh
```

Этот скрипт:
- Создает Python virtual environment
- Устанавливает зависимости Python
- Создает .env файл
- Устанавливает зависимости Node.js

## Шаг 2: Запуск PostgreSQL

```bash
docker-compose up -d
```

Проверьте, что контейнер запущен:
```bash
docker-compose ps
```

Вы должны увидеть контейнер `csv_to_db_postgres` в статусе `running`.

## Шаг 3: Запуск Backend

### Windows
```bash
cd backend
venv\Scripts\activate
python -m uvicorn app.main:app --reload
```

### MacOS/Linux
```bash
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload
```

Я должен увидеть сообщение:
```
Uvicorn running on http://0.0.0.0:8000
```

## Шаг 4: Запуск Frontend

В другом терминале:
```bash
cd frontend
npm run dev
```

Вы должны увидеть:
```
  VITE v5.0.0  ready in XXX ms

  ➜  Local:   http://localhost:5173/
```

## Шаг 5: Доступ к приложению

Откройте браузер и перейдите на `http://localhost:5173`

## Тестирование

### 1. Регистрация
- Нажмите "Зарегистрироваться"
- Заполните данные:
  - Username: `testuser`
  - Email: `test@example.com`
  - Password: `password123`
- Нажмите "Регистрация"

### 2. Вход
- Введите username: `testuser`
- Введите password: `password123`
- Нажмите "Вход"

### 3. Создание таблицы

Вкладка "Создать таблицу":

**Таблица "users":**
| Название | Тип | Nullable | Unique |
|----------|-----|----------|--------|
| name | varchar | No | No |
| email | varchar | No | Yes |
| age | integer | Yes | No |
| created_date | date | Yes | No |

### 4. Импорт CSV

Вкладка "Импорт CSV":
1. Выберите таблицу: `users`
2. Загрузите файл из `examples/users_example.csv`
3. Сопоставьте колонки:
   - `first_name` → `name`
   - `email` → `email`
   - `age` → `age`
   - `join_date` → `created_date`
4. Нажмите "Импортировать"

### 5. Проверка результата

- Вкладка "Таблицы" покажет список таблиц
- Приложение должно указать количество импортированных строк

## Остановка приложения

### Остановка Frontend
```
Ctrl+C в терминале Frontend
```

### Остановка Backend
```
Ctrl+C в терминале Backend
```

### Остановка PostgreSQL
```bash
docker-compose down
```

Если вы хотите удалить данные:
```bash
docker-compose down -v
```

## Решение проблем

### Ошибка: "could not connect to server"
```
Проверьте что PostgreSQL запущен: docker-compose ps
```

### Ошибка: "Port already in use"
```
Backend: Измените порт в uvicorn команде: --port 8001
Frontend: Измените порт в vite.config.ts

Или убейте процессы:
Windows: netstat -ano | findstr :8000
Linux/Mac: lsof -i :8000
```

### Ошибка модуля при запуске Backend
```
Убедитесь что virtual environment активирован
Windows: venv\Scripts\activate
Linux/Mac: source venv/bin/activate

Переустановите зависимости:
pip install -r requirements.txt
```

### CORS ошибки
```
Убедитесь что Backend запущен на http://localhost:8000
Проверьте что Frontend на http://localhost:5173
```

## API Документация

При запущенном Backend версию можно просмотреть на:
```
http://localhost:8000/docs
```

Это Swagger UI с интерактивной документацией всех endpoints.

## Файлы для тестирования

В папке `examples/` находятся примеры CSV файлов:

- `users_example.csv` - Пример таблицы users
- `products_example.csv` - Пример таблицы products

Вы можете использовать их для тестирования импорта.

## Переменные окружения

### Backend (.env)
```
DATABASE_URL=postgresql://user:password@localhost:5432/csv_to_db
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Frontend (.env)
```
VITE_API_URL=http://localhost:8000/api
```

## Далее

Для развертывания в production и дополнительной информации смотрите [README.md](../README.md)
