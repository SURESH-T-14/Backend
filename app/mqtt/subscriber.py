import json
import logging

from pydantic import ValidationError

import paho.mqtt.client as mqtt

from app.core.config import get_settings
from app.database.session import SessionLocal
from app.models.vehicle import Vehicle
from app.schemas.gps import GpsIngestPayload
from app.services.ingest_service import store_gps_reading

logger = logging.getLogger("gps_tracking.mqtt")


class MqttSubscriber:
    """Background MQTT subscriber that ingests GPS readings into PostgreSQL.

    Runs paho-mqtt's own network loop in a background thread (loop_start), so it
    never touches FastAPI's asyncio event loop. Each message gets its own short-lived
    SQLAlchemy session, since callbacks fire on the paho thread, not a request thread.
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id="gps-tracking-backend",
        )
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message
        # Backoff between reconnect attempts if the broker connection drops.
        self._client.reconnect_delay_set(min_delay=1, max_delay=30)

    def start(self) -> None:
        self._client.connect_async(self._settings.mqtt_host, self._settings.mqtt_port)
        self._client.loop_start()
        logger.info(
            "MQTT subscriber starting, connecting to %s:%s",
            self._settings.mqtt_host,
            self._settings.mqtt_port,
        )

    def stop(self) -> None:
        self._client.loop_stop()
        self._client.disconnect()

    def _on_connect(self, client, userdata, flags, reason_code, properties=None) -> None:
        if reason_code == 0:
            logger.info("MQTT connected, subscribing to %s", self._settings.mqtt_topic_pattern)
            client.subscribe(self._settings.mqtt_topic_pattern, qos=1)
        else:
            logger.error("MQTT connection failed: %s", reason_code)

    def _on_disconnect(self, client, userdata, flags, reason_code, properties=None) -> None:
        logger.warning("MQTT disconnected (reason=%s); paho will retry automatically", reason_code)

    def _on_message(self, client, userdata, msg: mqtt.MQTTMessage) -> None:
        try:
            raw = json.loads(msg.payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            logger.warning("Discarding malformed (non-JSON) message on %s", msg.topic)
            return

        try:
            payload = GpsIngestPayload.model_validate(raw)
        except ValidationError as exc:
            logger.warning("Discarding invalid GPS payload on %s: %s", msg.topic, exc)
            return

        db = SessionLocal()
        try:
            vehicle = db.query(Vehicle).filter(Vehicle.vehicle_number == payload.vehicle_id).first()
            if vehicle is None:
                logger.warning("Discarding GPS reading for unknown vehicle '%s'", payload.vehicle_id)
                return
            store_gps_reading(db, vehicle_id=vehicle.id, payload=payload)
            db.commit()
            logger.info(
                "Stored GPS reading for %s: (%.5f, %.5f) speed=%.1f",
                payload.vehicle_id,
                payload.latitude,
                payload.longitude,
                payload.speed,
            )
        except Exception:
            db.rollback()
            logger.exception("Failed to store GPS reading for %s", payload.vehicle_id)
        finally:
            db.close()
