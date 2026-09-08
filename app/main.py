import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import auth, routes, tracking, users, vehicles
from app.mqtt.subscriber import MqttSubscriber

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("gps_tracking")

mqtt_subscriber = MqttSubscriber()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        mqtt_subscriber.start()
    except Exception:
        # The API must stay usable even if the broker is temporarily unreachable
        # at startup; the subscriber retries connecting in the background.
        logger.exception("MQTT subscriber failed to start")
    yield
    mqtt_subscriber.stop()


app = FastAPI(
    title="GPS Vehicle Tracking API",
    description="Backend for a GPS-based bus/vehicle tracking system with per-user route/vehicle authorization.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(routes.router)
app.include_router(vehicles.router)
app.include_router(tracking.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Never leak stack traces or internals to the client."""
    logger.exception("Unhandled error while processing %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


@app.get("/health", tags=["health"], summary="Liveness check")
def health() -> dict[str, str]:
    return {"status": "ok"}
