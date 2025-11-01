from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.core.config import settings
import uvicorn
from pathlib import Path

Path("data/input").mkdir(parents=True, exist_ok=True)
Path("data/output").mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Excel AI Engine",
    description="Natural language interface for Excel data analysis using LLMs. Supports math operations, aggregations, filtering, date operations, pivots, unpivots, joins, and text analysis.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "Excel AI Engine Support",
        "url": "https://github.com/your-repo/excel-ai-engine"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1", tags=["Excel AI"])

@app.get("/")
async def root():
    return {
        "message": "Excel AI Engine API",
        "version": "1.0.0",
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc"
        },
        "health_check": "/api/v1/health",
        "features": [
            "Natural language querying",
            "Math operations",
            "Aggregations",
            "Filtering",
            "Date operations",
            "Pivot tables",
            "Unpivot operations",
            "Multi-file joins",
            "Text analysis"
        ]
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )