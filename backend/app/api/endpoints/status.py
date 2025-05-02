# app/api/endpoints/status.py
from fastapi import APIRouter, Depends, HTTPException, status as http_status, Response
from loguru import logger
import uuid
from redis.asyncio import Redis
import asyncio
from datetime import datetime, timezone, date, time
import time as process_time
from typing import Dict, Optional, Literal
from pydantic import BaseModel, Field
from celery.exceptions import OperationalError as CeleryOperationalError

# Core components
from app.core.logging_config import trace_id_var
from app.core.database import get_database, get_redis_client, AsyncIOMotorDatabase
from app.worker.celery_app import celery_app

# Repositories for metrics
try:
    from app.modules.people.repository import UserRepository, get_user_repository
    from app.modules.sales.repository import OrderRepository, get_order_repository
except ImportError:
    logger.error("Failed to import repositories for metrics endpoint. Metrics will be limited.")
    UserRepository = None
    OrderRepository = None
    async def get_user_repository(): return None
    async def get_order_repository(): return None

class ComponentStatus(BaseModel):
    status: Literal["ok", "error", "unavailable"] = "ok"
    message: Optional[str] = None

class HealthCheckResponse(BaseModel):
    overall_status: Literal["ok", "error"] = "ok"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    uptime_seconds: float = Field(..., description="Process uptime in seconds")
    components: Dict[str, ComponentStatus]

class BasicMetricsResponse(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    active_users: Optional[int] = None
    orders_today: Optional[int] = None

PROCESS_START_TIME = process_time.monotonic()

router = APIRouter()

@router.get(
    "/healthcheck",
    response_model=HealthCheckResponse,
    tags=["Status & Health"],
    summary="Application Health and Component Status Check"
)
async def get_application_health(
    db: Optional[AsyncIOMotorDatabase] = Depends(get_database),
    redis: Optional[Redis] = Depends(get_redis_client)
):
    trace_id = trace_id_var.get() or f"health_{uuid.uuid4().hex[:8]}"
    log = logger.bind(trace_id=trace_id, api_endpoint="/healthcheck GET")
    log.info("Performing application health check...")

    component_statuses: Dict[str, ComponentStatus] = {}
    critical_ok = True

    if db:
        try:
            await db.command('ping')
            component_statuses["database_mongodb"] = ComponentStatus(status="ok")
            log.debug("MongoDB ping successful.")
        except Exception as e:
            err_msg = f"MongoDB connection check failed: {e}"
            log.error(err_msg)
            component_statuses["database_mongodb"] = ComponentStatus(status="error", message=err_msg)
            critical_ok = False
    else:
        log.error("MongoDB connection not available.")
        component_statuses["database_mongodb"] = ComponentStatus(status="error", message="DB Client not available")
        critical_ok = False

    if redis:
        try:
            await redis.ping()
            component_statuses["cache_broker_redis"] = ComponentStatus(status="ok")
            log.debug("Redis ping successful.")
        except Exception as e:
            err_msg = f"Redis connection check failed: {e}"
            log.error(err_msg)
            component_statuses["cache_broker_redis"] = ComponentStatus(status="error", message=err_msg)
            critical_ok = False
    else:
        log.error("Redis connection not available.")
        component_statuses["cache_broker_redis"] = ComponentStatus(status="error", message="Redis Client not available")
        critical_ok = False

    celery_status = ComponentStatus(status="unavailable", message="Check not run or failed.")
    try:
        inspector = celery_app.control.inspect(timeout=1.5)
        ping_results = inspector.ping()
        if ping_results:
            celery_status = ComponentStatus(status="ok", message=f"{len(ping_results)} worker(s) responded.")
            log.debug("Celery worker ping successful.")
        else:
            celery_status = ComponentStatus(status="unavailable", message="No workers responded to ping.")
    except CeleryOperationalError as e:
        err_msg = f"Celery broker connection error during ping: {e}"
        log.error(err_msg)
        celery_status = ComponentStatus(status="error", message="Broker connection error")
        critical_ok = False
    except Exception as e:
        err_msg = f"Celery worker check failed unexpectedly: {e}"
        log.error(err_msg)
        celery_status = ComponentStatus(status="error", message="Ping check error")

    component_statuses["celery_workers"] = celery_status

    uptime_seconds = process_time.monotonic() - PROCESS_START_TIME
    overall_status: Literal["ok", "error"] = "ok" if critical_ok else "error"

    response_payload = HealthCheckResponse(
        overall_status=overall_status,
        uptime_seconds=uptime_seconds,
        components=component_statuses
    )

    status_code = http_status.HTTP_200_OK if critical_ok else http_status.HTTP_503_SERVICE_UNAVAILABLE
    return Response(
        content=response_payload.model_dump_json(exclude_none=True),
        status_code=status_code,
        media_type="application/json"
    )

@router.get(
    "/metrics",
    response_model=BasicMetricsResponse,
    tags=["Status & Health"],
    summary="Get basic application metrics (synchronous)",
)
async def get_basic_metrics(
    user_repo: Optional[UserRepository] = Depends(get_user_repository),
    order_repo: Optional[OrderRepository] = Depends(get_order_repository),
):
    log = logger.bind(api_endpoint="/metrics GET")
    log.info("Calculating basic metrics...")

    metrics = BasicMetricsResponse(active_users=None, orders_today=None)

    try:
        if user_repo:
            try:
                metrics.active_users = await user_repo.count({"is_active": True})
            except Exception as e:
                log.warning(f"Failed to count active users: {e}")
        else:
            log.warning("User repository not available for metrics.")

        if order_repo:
            try:
                today_start = datetime.combine(date.today(), time.min, tzinfo=timezone.utc)
                today_end = datetime.combine(date.today(), time.max, tzinfo=timezone.utc)
                metrics.orders_today = await order_repo.count({
                    "created_at": {"$gte": today_start, "$lte": today_end}
                })
            except Exception as e:
                log.warning(f"Failed to count orders today: {e}")
        else:
            log.warning("Order repository not available for metrics.")

        log.info(f"Basic metrics calculated: {metrics.model_dump(exclude_none=True)}")
        return metrics

    except Exception as e:
        log.exception("Unexpected error during basic metrics calculation.")
        raise HTTPException(status_code=500, detail="Internal server error calculating metrics.")