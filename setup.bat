@echo off
echo ========================================
echo Export CSV to DB - Setup Script
echo ========================================
echo.

echo Creating Python virtual environment...
cd backend
python -m venv venv
call venv\Scripts\activate

echo Installing Python dependencies...
pip install -r requirements.txt

echo.
echo ========================================
echo Creating .env file...
if not exist .env (
    copy .env.example .env
    echo .env file created from .env.example
    echo Please edit .env with your database credentials
)

cd ..

echo.
echo Installing Node dependencies...
cd frontend
call npm install
cd ..

echo.
echo ========================================
echo Setup complete!
echo.
echo Next steps:
echo 1. Start PostgreSQL: docker-compose up -d
echo 2. Start Backend: cd backend && venv\Scripts\activate && python -m uvicorn app.main:app --reload
echo 3. Start Frontend: cd frontend && npm run dev
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo Docs: http://localhost:8000/docs
echo ========================================
