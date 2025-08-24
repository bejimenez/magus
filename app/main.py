# run with uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# for production run uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000

import time
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import get_settings

from app.api.v1.routes import router as v1_router

from app.models.database import engine, Base, SessionLocal

from app.services.culture_loader import CultureLoader
from app.services.cache_service import CacheService

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s -%(message)s',
    handler=[
        logging.StreamHandler(),
        logging.FileHandler('name_generator.log')
    ]
)
logger = logging.getLogger(__name__)

# App lifecycle
async def lifespan(app: FastAPI):

    logger.info("Starting Magus API")

    settings = get_settings()
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Database: {settings.database_url}")

    try:
        logger.info("Initializing database")
        Base.metadata.create_all(bind=engine)
        
        # verify db has seed data
        with SessionLocal() as db:
            from app.models.database import Culture
            culture_count = db.query(Culture).count()

            if culture_count == 0:
                logger.warning("No cultures found in database!")
                logger.warning("Run: python scripts/seed_database.py")
            else:
                logger.info(f"Databse ready with {culture_count} cultures")   

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

    try:
        logger.info("Loading culture templates")
        culture_loader = CultureLoader()
        app.state.cultures = culture_loader.load_all_cultures()
        logger.info(f"Loaded {len(app.state.cultures)} culture templates")

    exception Exception as e:
        logger.error(f"Failed to load cultures: {e}")
        raise

    try:
        logger.info("Initializing cache service")
        app.state.cache = CacheService(settings)
        await app.state.cache.initialize()
        logger.info("Cache service ready.")

    except Exception as e:
        logger.error(f"Cache Initialization failed: {e}")
        # Cache is optional
        app.state.cache = None

    # Load ML models here when implemented
    # app.state.ml_model = load_model()

    logger.info("Magus API ready to serve requests.")
    logger.info(f"Documentation available at http://localhost:8000/docs")

    yield

    # --- SHUTDOWN ---
    logger.info("Shutting down Magus API")

    if hasattr(app.state, 'cache') and app.state.cache:
        await app.state.cache.close()

    engine.dispose()

    logger.info ("Shutdown complete")

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="""
    An intelligent, culturally-aware name generation service for storytelling.

    Features:
    - Multiple cultures
    - Gender-aware patterns
    - Pronunciation guides
    - Quality scoring
    - High performance

    Generate names by specifying culture, gender, and other params.
    Names are scored for quality and cached for performance.
    """,    
    version=settings.version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
    lifespan=lifespan
)

# configure for frontend domains when/if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins="http://localhost:3000",
    allow_credentials=True,
    allow_methods=["Get", "POST"],
    allow_headers=["*"],
    expose_headers=[X-Total-Count", "X-Generation-Time-Ms"]
)

if settings.environment == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.allowed_hosts # "api.magus.com"
    )

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    import uuid # unique ID for debugging
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id

    logger.info(f"[{request_id}] {request.method} {request.url.path}")

    start_time = time.time()
    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = str(round(process_time, 2))

    logger.info(f"[{request_id}] Completed in {process_time:.2f}ms - Status: {response.status_code}")
    return response

@app.middleware("http")
async def monitor_performance(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000

    if process_time > settings.slow_request_threshold_ms:
        logger.warning(
            f"Slow request: {request.method} {request.url.path} "
            f"took {process_time:.2f}ms"
        )

    return response

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.detail,
                "status_code": exc.status_code,
                "request_id": getattr(request.state, 'request_id', None)
            }
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        errors.append({
                          "field": ".".join(str(loc) for loc in error["loc"][1:]),
                          "message": error["msg"],
                          "type": error["type"]
                      })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "message": "Validation failed",
                "status_code": 422,
                "request_id": getattr(request.state, 'request_id', None),
                "validation_errors": errors
            }
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, 'request_id', None)

    logger.error(
        f"[{request_id}] Unhandled exception: {exc}",
        exc_info=True
    )

    if settings.environment == "production":
        message = "An internal error occurred"
    else:
        message = str(exc)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "message": message,
                "status_code": 500,
                "request_id": request_id
            }
        }
    )

app.include_router(
    v1_router,
    prefix=settings.api_v1_prefix,
    tags=["v1"]
)

@app.get("/", tags=["root"])
async def root():
    return {
        "name": settings.app_name,
        "version": settings.version,
        "status": "health",
        "documentation": "/docs",
        "api": {
            "v1": settings.api_v1_prefix
        }
    }

@app.get("/health", tags=["monitoring"])
async def health_check():
    health_status = {
        "status": "health",
        "timestamp": time.time(),
        "version": settings.version,
        "components": {}
    }

    try:
        with SessionLocal() as db:
            db.execute("SELECT 1")
        health_status["components"]["database"] = "healthy"
    except Exception as e:
        health_status["components"]["database"] = "unhealthy"
        health_status["status"] = "degraded"
        logger.error(f"Database health check failed: {e}")

    if hasattr(app.state, 'cache') and app.state.cache:
        try:
            await app.state.cache.ping()
            health_status["components"]["cache"] = "healthy"
        except Exception as e:
            health_status["components"]["cahce"] = "unhealthy"
            # cache is optional so dont degrade status
            logger.warning(f"Cache health check failed: {e}")

    else:
        health_status["components"]["cache"] = "not configured"


    if hasattr(app.state, 'cultures'):
        culture_count = len(app.state.cultures)
        if culture_count > 0:
            health_status["components"]["cultures"] = f"healthy ({culture_count} loaded)"
        else:
            health_status["components"]["cultures"] = "unhealthy (none loaded)"
            health_status["status"] = "unhealthy"

    else:
        health_status["components"]["cultures"] = "not loaded"
        health_status["status"] = "unhealthy"

    status_code = status.HTTP_200_OK if health_status["status"] == "healthy" else status.HTTP.503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content=health_status
    )
