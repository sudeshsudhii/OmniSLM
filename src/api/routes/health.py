"""
OmniSLM Health Check Routes — /healthz, /readyz
"""

from __future__ import annotations

import time

from fastapi import APIRouter, Response, status

from src.api.dependencies import get_default_runtime
from src.config.settings import get_settings
from src.infrastructure.cache.redis_client import check_redis_health

router = APIRouter(tags=["Health"])
settings = get_settings()

_start_time = time.time()


@router.get("/healthz", summary="Liveness probe")
async def liveness() -> dict:
    """Basic liveness check — is the process running?"""
    return {
        "status": "alive",
        "version": settings.app_version,
        "uptime_seconds": int(time.time() - _start_time),
    }


@router.get("/readyz", summary="Readiness probe")
async def readiness(response: Response) -> dict:
    """Readiness check — can the service handle traffic?

    Checks PostgreSQL, Redis, and default runtime connectivity.
    """
    checks = {}
    all_healthy = True

    # Redis
    try:
        redis_ok = await check_redis_health()
        checks["redis"] = {"status": "healthy" if redis_ok else "unhealthy"}
        if not redis_ok:
            all_healthy = False
    except Exception as e:
        checks["redis"] = {"status": "unhealthy", "error": str(e)}
        all_healthy = False

    # Default Runtime
    try:
        runtime = get_default_runtime()
        runtime_ok = await runtime.is_available()
        checks[runtime.provider_name] = {"status": "healthy" if runtime_ok else "unhealthy"}
        if not runtime_ok:
            all_healthy = False
    except Exception as e:
        checks["runtime"] = {"status": "unhealthy", "error": str(e)}
        all_healthy = False

    overall_status = "ready" if all_healthy else "not_ready"

    if not all_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": overall_status,
        "version": settings.app_version,
        "environment": settings.environment,
        "checks": checks,
    }
