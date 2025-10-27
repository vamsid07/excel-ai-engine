"""
Main FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import routes
from pathlib import Path

# Create FastAPI app
app = FastAPI(
    title="Excel AI Engine",
    description="AI-powered Excel data analysis and manipulation engine",
    version="4.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(routes.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "api_version": "4.0.0",
        "debug_mode": settings.DEBUG,
        "features": {
            "web_ui": True,
            "natural_language_queries": True,
            "multi_file_joins": True,
            "batch_processing": True,
            "export": True,
            "history": True
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )