
"""
This module provides a simple FastAPI web application that returns system information
and uptime details. Ideally suited for DevOps monitoring labs.
"""

import os
import socket
import platform
import logging
import json
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest


HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint", "status_code"],
)

HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed",
    ["method", "endpoint"],
)

DEVOPS_INFO_ENDPOINT_CALLS_TOTAL = Counter(
    "devops_info_endpoint_calls_total",
    "Total calls to application endpoints",
    ["endpoint"],
)

DEVOPS_INFO_SYSTEM_COLLECTION_SECONDS = Histogram(
    "devops_info_system_collection_seconds",
    "Time spent collecting system information",
)

class JSONFormatter(logging.Formatter):
    """Render logs in JSON format for log aggregation systems."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        context_fields = (
            "event",
            "method",
            "path",
            "status_code",
            "client_ip",
            "user_agent",
            "duration_ms",
        )
        for field in context_fields:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, separators=(",", ":"))


def configure_logging() -> None:
    """Configure root logger to emit single-line JSON records."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = [handler]


configure_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_: FastAPI):
    """Emit startup metadata once to verify structured logging startup event."""
    logger.info(
        "Application startup complete",
        extra={
            "event": "startup",
            "status_code": 200,
        },
    )
    yield


app = FastAPI(title="DevOps Info Service", lifespan=lifespan)

# Start time for uptime calculation
START_TIME = datetime.now(timezone.utc)


def normalize_endpoint(request: Request) -> str:
    """Return low-cardinality endpoint labels for metrics."""
    route = request.scope.get("route")
    if route is not None and getattr(route, "path", None):
        return route.path
    return "unmatched"

def get_uptime():
    """Calculate the uptime of the application."""
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        'seconds': seconds,
        'human': f"{hours} hours, {minutes} minutes"
    }

def get_system_info():
    """Retrieve system-level information."""
    return {
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        'platform_version': platform.version(),
        'architecture': platform.machine(),
        'cpu_count': os.cpu_count(),
        'python_version': platform.python_version()
    }


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Log each request and response with context for observability."""
    start = time.perf_counter()
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    endpoint = normalize_endpoint(request)
    in_progress = HTTP_REQUESTS_IN_PROGRESS.labels(method=request.method, endpoint=endpoint)
    in_progress.inc()

    try:
        response = await call_next(request)
    except Exception:  # pylint: disable=broad-exception-caught
        duration_seconds = time.perf_counter() - start
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        HTTP_REQUESTS_TOTAL.labels(
            method=request.method,
            endpoint=endpoint,
            status_code="500",
        ).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(
            method=request.method,
            endpoint=endpoint,
            status_code="500",
        ).observe(duration_seconds)
        logger.exception(
            "Unhandled request exception",
            extra={
                "event": "http_error",
                "method": request.method,
                "path": endpoint,
                "status_code": 500,
                "client_ip": client_ip,
                "user_agent": user_agent,
                "duration_ms": duration_ms,
            },
        )
        in_progress.dec()
        return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

    duration_seconds = time.perf_counter() - start
    duration_ms = round(duration_seconds * 1000, 2)
    status_code = str(response.status_code)
    HTTP_REQUESTS_TOTAL.labels(
        method=request.method,
        endpoint=endpoint,
        status_code=status_code,
    ).inc()
    HTTP_REQUEST_DURATION_SECONDS.labels(
        method=request.method,
        endpoint=endpoint,
        status_code=status_code,
    ).observe(duration_seconds)
    logger.info(
        "HTTP request processed",
        extra={
            "event": "http_request",
            "method": request.method,
            "path": endpoint,
            "status_code": response.status_code,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "duration_ms": duration_ms,
        },
    )
    in_progress.dec()
    return response

@app.get("/")
async def root(request: Request):
    """
    Main endpoint returning service and system information.
    """
    DEVOPS_INFO_ENDPOINT_CALLS_TOTAL.labels(endpoint="/").inc()
    uptime = get_uptime()
    with DEVOPS_INFO_SYSTEM_COLLECTION_SECONDS.time():
        system_info = get_system_info()

    return {
        "service": {
            "name": "devops-info-service",
            "version": "1.0.0",
            "description": "DevOps course info service",
            "framework": "FastAPI"
        },
        "system": system_info,
        "runtime": {
            "uptime_seconds": uptime['seconds'],
            "uptime_human": uptime['human'],
            "current_time": datetime.now(timezone.utc).isoformat(),
            "timezone": "UTC"
        },
        "request": {
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get('user-agent'),
            "method": request.method,
            "path": request.url.path
        },
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/health", "method": "GET", "description": "Health check"},
            {"path": "/metrics", "method": "GET", "description": "Prometheus metrics"}
        ]
    }

@app.get("/health")
async def health():
    """
    Health check endpoint.
    """
    DEVOPS_INFO_ENDPOINT_CALLS_TOTAL.labels(endpoint="/health").inc()
    return {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'uptime_seconds': get_uptime()['seconds']
    }


@app.get("/metrics")
async def metrics():
    """Expose Prometheus metrics."""
    DEVOPS_INFO_ENDPOINT_CALLS_TOTAL.labels(endpoint="/metrics").inc()
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5000"))
    uvicorn.run(app, host=host, port=port, log_config=None, access_log=False)
