import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.api.v1.router import router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.discovery.errors import DiscoveryError
from app.discovery.execution import DiscoveryExecutor

configure_logging()
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(application: FastAPI):
    application.state.discovery_executor = DiscoveryExecutor(settings)
    try:
        yield
    finally:
        application.state.discovery_executor.close()


app = FastAPI(
    lifespan=lifespan,
    title="SkillSphere V3 API",
    version="0.1.0",
    default_response_class=ORJSONResponse,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "%s %s completed status=%s duration_ms=%.2f",
        request.method,
        request.url.path,
        response.status_code,
        (time.perf_counter() - started) * 1000,
        extra={"request_id": request_id},
    )
    return response


app.include_router(router)


@app.exception_handler(DiscoveryError)
async def discovery_error_handler(request: Request, exc: DiscoveryError):
    return ORJSONResponse(
        status_code=exc.status_code, content={"detail": {"code": exc.code, "message": str(exc)}}
    )
