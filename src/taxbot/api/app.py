"""FastAPI application with middleware and health checks."""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from ..core.config import get_settings
from ..core.logging import get_api_logger, setup_logging
from ..storage.csv_repository import CsvRepository
from .routes import admin, concepts


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    setup_logging()
    logger = get_api_logger()
    logger.info("Starting TaxBot API server")
    
    # Initialize repository
    app.state.repository = CsvRepository()
    
    yield
    
    # Shutdown
    logger.info("Shutting down TaxBot API server")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title="TaxBot Enterprise API",
        description="Enterprise-grade DIAN concepts scraper and analyzer",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    
    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Add request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log HTTP requests."""
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log request
        logger = get_api_logger()
        logger.info(
            f"{request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.3f}s"
        )
        
        # Add timing header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
    
    # Add error handling middleware
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Global exception handler."""
        logger = get_api_logger()
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": "An unexpected error occurred",
                "request_id": getattr(request.state, "request_id", None),
            }
        )
    
    # Include routers
    app.include_router(concepts.router, prefix="/api/v1", tags=["concepts"])
    app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
    
    # Health check endpoint
    @app.get("/health", tags=["health"])
    async def health_check():
        """Health check endpoint."""
        try:
            # Check repository
            repo = app.state.repository
            concept_count = repo.get_concept_count()
            
            return {
                "status": "healthy",
                "timestamp": time.time(),
                "version": "1.0.0",
                "concepts": concept_count,
                "services": {
                    "database": "healthy",
                    "api": "healthy",
                }
            }
        except Exception as e:
            logger = get_api_logger()
            logger.error(f"Health check failed: {e}")
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "timestamp": time.time(),
                    "error": str(e),
                }
            )
    
    # Metrics endpoint
    @app.get("/metrics", tags=["health"])
    async def metrics():
        """Basic metrics endpoint."""
        try:
            repo = app.state.repository
            concept_count = repo.get_concept_count()
            themes = repo.get_themes()
            
            return {
                "concepts": {
                    "total": concept_count,
                    "themes": len(themes),
                },
                "api": {
                    "version": "1.0.0",
                    "uptime": time.time(),  # This should be actual uptime
                }
            }
        except Exception as e:
            logger = get_api_logger()
            logger.error(f"Metrics collection failed: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": "Failed to collect metrics"}
            )
    
    return app


# Create app instance
app = create_app()
