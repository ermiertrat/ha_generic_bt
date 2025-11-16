"""Support for Generic BT binary sensor."""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, Schema
from .coordinator import GenericBTCoordinator
from .entity import GenericBTEntity


# Initialize the logger
_LOGGER = logging.getLogger(__name__)
PARALLEL_UPDATES = 0


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up Generic BT device based on a config entry."""
    coordinator: GenericBTCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([GenericBTBinarySensor(coordinator)])

    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service("write_gatt", Schema.WRITE_GATT.value, "write_gatt")
    platform.async_register_entity_service("read_gatt", Schema.READ_GATT.value, "read_gatt")
    platform.async_register_entity_service("try_connect",Schema.TRY_CONNECT.value,"try_connect")
    platform.async_register_entity_service("disconnect",Schema.DISCONNECT.value,"disconnect")
    

class GenericBTBinarySensor(GenericBTEntity, BinarySensorEntity):
    """Representation of a Generic BT Binary Sensor."""

    _attr_name = None

    def __init__(self, coordinator: GenericBTCoordinator) -> None:
        """Initialize the Device."""
        super().__init__(coordinator)

    @property
    def is_on(self):
        return self._device.connected

    async def write_gatt(self, target_uuid, data, force_reconnect, wake_before_write):
        await self._device.write_gatt(target_uuid, data, force_reconnect, wake_before_write)
        self.async_write_ha_state()

    async def read_gatt(self, target_uuid):
        await self._device.read_gatt(target_uuid)
        self.async_write_ha_state()
    async def try_connect(self):
        await self._device.try_connect()
        self.async_write_ha_state()

    async def disconnect(self,force_disconnect):
        await self._device.disconnect(force=force_disconnect)
        self.async_write_ha_state()

        


