"""Constants"""
import voluptuous as vol
from enum import Enum

from homeassistant.helpers.config_validation import make_entity_service_schema
import homeassistant.helpers.config_validation as cv

DOMAIN = "ha_ble_controller"
DEVICE_STARTUP_TIMEOUT_SECONDS = 30

class Schema(Enum):
    """General used service schema definition"""

    WRITE_GATT = make_entity_service_schema(
        {
            vol.Required("target_uuid"): cv.string,
            vol.Required("data"): cv.string,
            vol.Optional("force_reconnect", default=False): cv.boolean,
            vol.Optional("wake_before_write", default=False): cv.boolean
        }
    )
    READ_GATT = make_entity_service_schema(
        {
            vol.Required("target_uuid"): cv.string
        }
    )
    TRY_CONNECT = make_entity_service_schema(
        {
        }
    )
    DISCONNECT = make_entity_service_schema(
        {
            vol.Required("force"): cv.boolean

        }
    )
