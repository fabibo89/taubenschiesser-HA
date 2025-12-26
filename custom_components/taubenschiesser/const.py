"""Constants for Taubenschiesser integration."""
from typing import Final

DOMAIN: Final = "taubenschiesser"
PLATFORMS: Final = ["sensor", "switch", "button"]

# Configuration keys
CONF_API_URL: Final = "api_url"
CONF_API_TOKEN: Final = "api_token"
CONF_MQTT_BROKER: Final = "mqtt_broker"
CONF_MQTT_PORT: Final = "mqtt_port"
CONF_MQTT_USERNAME: Final = "mqtt_username"
CONF_MQTT_PASSWORD: Final = "mqtt_password"

# Defaults
DEFAULT_MQTT_PORT: Final = 1883
DEFAULT_UPDATE_INTERVAL: Final = 30

# API endpoints
API_ENDPOINT_DEVICES: Final = "/api/devices"
API_ENDPOINT_CONTROL: Final = "/api/device-control"
API_ENDPOINT_AUTH: Final = "/api/auth/login"

# MQTT topics
MQTT_TOPIC_COMMAND: Final = "taubenschiesser/{ip}"
MQTT_TOPIC_STATUS: Final = "taubenschiesser/{ip}/info"

# Device attributes
ATTR_ROTATION: Final = "rotation"
ATTR_TILT: Final = "tilt"
ATTR_MONITOR_STATUS: Final = "monitor_status"
ATTR_DEVICE_IP: Final = "device_ip"
ATTR_LAST_SEEN: Final = "last_seen"
ATTR_MOVING: Final = "moving"

# Monitor status values
MONITOR_STATUS_RUNNING: Final = "running"
MONITOR_STATUS_PAUSED: Final = "paused"
MONITOR_STATUS_STOPPED: Final = "stopped"

