
# Versão final com auth real, rate limit, handlers e lifecycle integrado
from fastapi import FastAPI, Request, status, Depends
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
from typing import Optional, List, Any, Union
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.core.config import settings
from app.core.logging_config import logger, trace_id_var
from app.db.mongo_client import connect_to_mongo, close_mongo_connection
from app.core.redis_client import connect_redis, close_redis, get_redis_client
from app.websocket.listeners import start_redis_command_listener, stop_redis_command_listener
from app.api.v1 import api_router
import asyncio, uuid, time
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone

class ErrorDetail(BaseModel):
    msg: str
    type: Optional[str] = None
    loc: Optional[List[Union[str, int]]] = None

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    trace_id = getattr(request.state, 'trace_id', 'N/A')
    log = logger.bind(trace_id=trace_id)
    log.warning(f"HTTP Exception Caught: {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content=ErrorDetail(msg=str(exc.detail), type="http_exception").model_dump())

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    trace_id = getattr(request.state, 'trace_id', 'N/A')
    log = logger.bind(trace_id=trace_id)
    log.warning(f"Validation Error: {exc.errors()}")
    return JSONResponse(status_code=422, content=ErrorDetail(msg="Validation Error", type="validation_error").model_dump())

async def generic_exception_handler(request: Request, exc: Exception):
    trace_id = getattr(request.state, 'trace_id', 'N/A')
    log = logger.bind(trace_id=trace_id)
    log.exception(f"Unhandled Exception: {exc}")
    return JSONResponse(status_code=500, content=ErrorDetail(msg="Internal error", type="unhandled_exception").model_dump())

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.PROJECT_NAME}...")
    await asyncio.gather(connect_to_mongo(), connect_redis())
    await start_redis_command_listener(get_redis_client())
    yield
    logger.info("Shutting down...")
    await asyncio.gather(stop_redis_command_listener(), close_mongo_connection(), close_redis())

limiter = Limiter(key_func=get_remote_address, default_limits=["500/minute"])

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    exception_handlers={
        StarletteHTTPException: http_exception_handler,
        RequestValidationError: validation_exception_handler,
        RateLimitExceeded: _rate_limit_exceeded_handler
    }
)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
    request.state.trace_id = trace_id
    trace_id_var.set(trace_id)
    start_time = time.time()
    log = logger.bind(trace_id=trace_id)
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Trace-ID"] = trace_id
    log.info(f"{request.method} {request.url.path} completed in {process_time:.2f}s")
    trace_id_var.set(None)
    return response

if settings.CORS_ORIGINS:
    app.add_middleware(CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS != "*" else ["*"],
        allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", tags=["Health Check"], include_in_schema=False)
async def read_root():
    return {"status": "ok", "project": settings.PROJECT_NAME, "timestamp": datetime.now(timezone.utc)}
