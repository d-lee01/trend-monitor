from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db, close_db
from app.api import auth, admin
from app.core.logging_config import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan event handler for startup/shutdown tasks."""
    # Startup
    print("=" * 50)
    print("FastAPI: Starting up trend-monitor API")

    # Initialize structured logging
    setup_logging(debug=settings.debug)
    logger = logging.getLogger(__name__)
    logger.info("Structured JSON logging initialized")

    print(f"FastAPI: Version {settings.app_version}")
    print(f"FastAPI: Debug mode: {settings.debug}")
    from app.database import engine
    if engine:
        print("FastAPI: Database connection available")
    else:
        print("FastAPI: WARNING - No database connection (DATABASE_URL not set)")
    print("=" * 50)
    yield
    # Shutdown
    await close_db()
    print("FastAPI: Shutting down - database connections closed")


app = FastAPI(
    title="trend-monitor API",
    description="Quantified trend monitoring system API",
    version=settings.app_version,
    lifespan=lifespan
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Catch-all exception handler to prevent raw tracebacks in production"""
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "message": str(exc) if settings.debug else "An error occurred"}
    )

# CORS Middleware (configure for frontend origin)
# Note: HTTPSRedirectMiddleware removed - Railway handles HTTPS termination
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
    return response


# Include routers
app.include_router(auth.router)
app.include_router(admin.router)


@app.get("/")
async def root():
    return {"message": "trend-monitor API", "status": "operational"}


@app.get("/health")
async def health_check():
    """Health check endpoint for Railway and monitoring services"""
    return {
        "status": "healthy",
        "service": settings.app_name + "-api",
        "version": settings.app_version
    }


@app.get("/health/db")
async def health_check_database(db: AsyncSession = Depends(get_db)):
    """Health check endpoint that verifies database connectivity."""
    try:
        # Execute simple query
        result = await db.execute(text("SELECT 1"))
        result.scalar()

        # Check if tables exist
        tables_result = await db.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
        """))
        tables = [row[0] for row in tables_result.fetchall()]

        return {
            "status": "healthy",
            "database": "connected",
            "tables": tables,
            "expected_tables": ["trends", "data_collections", "users", "api_quota_usage"],
            "tables_exist": all(t in tables for t in ["trends", "data_collections", "users", "api_quota_usage"])
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "connection_failed",
            "error": str(e)
        }
