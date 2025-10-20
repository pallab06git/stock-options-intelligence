# © 2025 Pallab Basu Roy. All rights reserved.
# This source code is proprietary and confidential.
# Unauthorized copying, modification, or commercial use is strictly prohibited.
# Repository: https://github.com/pallab06/stock-options-intelligence

"""
Main FastAPI application entry point
"""

from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, make_asgi_app

from src.config.settings import get_settings

# Metrics
REQUEST_COUNT = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint"])
REQUEST_LATENCY = Histogram("http_request_duration_seconds", "HTTP request latency")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore
    """Application lifespan manager"""
    # Startup
    print("Starting Stock Options Intelligence...")
    print(f"Environment: {settings.environment}")
    # Initialize services here (database, Redis, etc.)
    yield
    # Shutdown
    print("Shutting down Stock Options Intelligence...")
    # Cleanup resources here


# Create FastAPI app
app = FastAPI(
    title="Stock Options Intelligence",
    description="AI-powered trading intelligence engine for SPY options",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint"""
    return {
        "message": "Stock Options Intelligence API",
        "version": "0.1.0",
        "status": "operational",
    }


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    # Add actual health checks here (database, Redis, external APIs)
    return {
        "status": "healthy",
        "environment": settings.environment,
        "version": "0.1.0",
    }


@app.get("/api/v1/signals")
async def get_signals() -> Dict[str, str]:
    """Get current trading signals"""
    # TODO: Implement signal retrieval
    return {
        "message": "Trading signals endpoint - to be implemented",
        "signals": [],
    }


@app.get("/api/v1/backtest")
async def run_backtest() -> Dict[str, str]:
    """Run historical backtest"""
    # TODO: Implement backtesting
    return {
        "message": "Backtesting endpoint - to be implemented",
    }


@app.get("/api/v1/models")
async def get_model_metrics() -> Dict[str, str]:
    """Get model performance metrics"""
    # TODO: Implement model metrics retrieval
    return {
        "message": "Model metrics endpoint - to be implemented",
        "models": [],
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):  # type: ignore
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):  # type: ignore
    """General exception handler"""
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.environment == "development",
    )
