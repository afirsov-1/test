#!/bin/bash

echo "========================================"
echo "Export CSV to DB - Setup Script"
echo "========================================"
echo ""

echo "Creating Python virtual environment..."
cd backend
python3 -m venv venv
source venv/bin/activate

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo ""
echo "========================================"
echo "Creating .env file..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo ".env file created from .env.example"
    echo "Please edit .env with your database credentials"
fi

cd ..

echo ""
echo "Installing Node dependencies..."
cd frontend
npm install
cd ..

echo ""
echo "========================================"
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Start PostgreSQL: docker-compose up -d"
echo "2. Start Backend: cd backend && source venv/bin/activate && python -m uvicorn app.main:app --reload"
echo "3. Start Frontend: cd frontend && npm run dev"
echo ""
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo "Docs: http://localhost:8000/docs"
echo "========================================"
