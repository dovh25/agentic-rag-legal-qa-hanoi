from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes.qa import router as qa_router
from src.core.config import get_settings
from src.core.logging import setup_logging

settings = get_settings()
setup_logging()

app = FastAPI(
    title=settings.APP_NAME,
    description="Agentic RAG Legal QA System for Hanoi Land Planning, Acquisition, Compensation & Resettlement.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in settings.CORS_ORIGINS.split(",")
        if origin.strip()
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(qa_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Health"])
async def root():
    return {
        "app": settings.APP_NAME,
        "status": "online",
        "docs": "/docs",
        "version": "0.1.0",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}
