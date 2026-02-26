from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.models import Base, engine
from app.routes import auth, tables

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="Export CSV to DB",
    description="Application for importing CSV files into PostgreSQL database",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(auth.router)
app.include_router(tables.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Export CSV to DB API",
        "documentation": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
