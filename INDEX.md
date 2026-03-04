# 📚 Export CSV to DB - Документация и Навигация

Добро пожаловать в проект "Export CSV to DB"! Это полнофункциональное веб-приложение для импорта CSV файлов в PostgreSQL.

## ✅ Актуальный статус (MVP+)

- Реализованы роли и права доступа (RBAC)
- Работает мастер CSV импорта + async импорт с прогрессом
- Есть CRUD строк, версионирование и rollback
- Добавлены аудит-логи в админке
- Добавлен слой подключений и active connection (мульти-БД)

> После pull/обновления схемы БД выполните миграции: `cd backend && alembic upgrade head`

## 🎯 Начните отсюда

### 🚀 Первый запуск (15 минут)
**👉 [QUICKSTART.md](QUICKSTART.md)** - Пошаговая инструкция по установке и первому запуску

### 📖 Полная документация
**👉 [README.md](README.md)** - Детальное описание функциональности, установки и использования

### 🏗️ Архитектура проекта
**👉 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Описание структуры кода и компонентов

### 🎉 Что готово?
**👉 [GETTING_STARTED.md](GETTING_STARTED.md)** - Резюме дoлов и инструкции

---

## 📋 Структура документации

```
├── QUICKSTART.md              ⭐ Начните отсюда
├── README.md                  📖 Полная документация
├── PROJECT_STRUCTURE.md       🏗️ Архитектура
├── GETTING_STARTED.md         🎉 Обзор функций
├── setup.bat                  🖥️ Автоматическая установка (Windows)
├── setup.sh                   🐧 Автоматическая установка (Linux/Mac)
└── INDEX.md                   📚 Этот файл
```

---

## 🎓 Рекомендуемый путь

### 1️⃣ Установка и запуск (15 мин)
```
QUICKSTART.md → setup.bat/sh → docker-compose up -d
```

### 2️⃣ Тестирование функциональности (10 мин)
```
примеры/users_example.csv → Создать таблицу → Импортировать CSV
```

### 3️⃣ Изучение архитектуры (30 мин)
```
PROJECT_STRUCTURE.md → Просмотр кода → Использование API
```

---

## 🔍 Поиск информации

### Я хочу...

**Запустить приложение**
→ [QUICKSTART.md#шаг-1-подготовка-окружения](QUICKSTART.md)

**Понять как работает приложение**
→ [README.md#функциональность](README.md)

**Посмотреть архитектуру кода**
→ [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

**Использовать API**
→ [README.md#api-endpoints](README.md)

**Развернуть в production**
→ [README.md#развертывание](README.md)

**Решить проблему**
→ [QUICKSTART.md#решение-проблем](QUICKSTART.md)

---

## 📦 Что у вас установится

### Backend
- **FastAPI 0.104** - Modern Python web framework
- **SQLAlchemy 2.0** - ORM для работы с БД
- **PostgreSQL** - Reliable database
- **JWT** - Безопасная аутентификация

### Frontend
- **React 18** - Modern UI library
- **TypeScript** - Type-safe JavaScript
- **Vite** - Lightning-fast build tool
- **Axios** - HTTP client

### Infrastructure
- **Docker** - Контейнеризация
- **Docker Compose** - Оркестрация сервисов
- **PostgreSQL 15** - Database container

---

## 📊 Основные компоненты

### 🔐 Аутентификация
- Регистрация с email
- Безопасный вход
- JWT токены
- Автоматический logout

### 📋 Создание таблиц
- Графический интерфейс
- Выбор типов данных
- Настройка колонок (nullable, unique)
- Автоматическое создание в БД

### 📁 Импорт CSV
- Загрузка файлов
- Сопоставление колонок
- Валидация данных
- Подробные отчеты об ошибках
- История импортов

---

## 🛠️ Автоматическая установка

### Windows
```bash
setup.bat
```

### Linux/Mac
```bash
chmod +x setup.sh
./setup.sh
```

---

## 🌐 Веб-интерфейс

```
Frontend:  http://localhost:5173
Backend:   http://localhost:8000
Docs API:  http://localhost:8000/docs
Database:  postgresql://user:password@localhost:5432/csv_to_db
```

---

## 📚 Дополнительные ресурсы

### Примеры CSV
- `examples/users_example.csv` - Пример таблицы users
- `examples/products_example.csv` - Пример таблицы products

### Docker
- `docker-compose.yml` - PostgreSQL сервис
- `Dockerfile.backend` - Backend контейнер
- `Dockerfile.frontend` - Frontend контейнер

### Конфигурация
- `.env.example` - Переменные окружения
- `package.json` - Node зависимости
- `requirements.txt` - Python зависимости

---

## ❓ FAQ

**Q: Как запустить приложение?**
A: Прочитайте [QUICKSTART.md](QUICKSTART.md)

**Q: Какие требования?**
A: Python 3.11+, Node 18+, Docker

**Q: Как импортировать CSV?**
A: Смотрите [README.md#импорт-csv](README.md)

**Q: Как создать таблицу без SQL?**
A: Используйте вкладку "Создать таблицу" в интерфейсе

**Q: Как развернуть в production?**
A: Смотрите [README.md#развертывание](README.md)

---

## 🎯 Основные ссылки

| Документ | Описание |
|----------|---------|
| [QUICKSTART.md](QUICKSTART.md) | ⭐⭐⭐ Начните отсюда |
| [README.md](README.md) | Полная документация |
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | Архитектура проекта |
| [GETTING_STARTED.md](GETTING_STARTED.md) | Обзор функций |

---

## 🚀 Следующие шаги

1. **Прочитайте** [QUICKSTART.md](QUICKSTART.md) (5 мин)
2. **Запустите** `setup.bat` или `setup.sh` (5 мин)
3. **Откройте** http://localhost:5173 (1 мин)
4. **Зарегистрируйтесь** и начните использовать (5 мин)

**Общее время: ~15-20 минут**

---

Успехов! 🎉 Если у вас есть вопросы - смотрите документацию или решение проблем в [QUICKSTART.md](QUICKSTART.md).
