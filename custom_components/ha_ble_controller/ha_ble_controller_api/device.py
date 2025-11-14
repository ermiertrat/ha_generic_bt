"""generic bt device"""

from uuid import UUID
import asyncio
import logging
from contextlib import AsyncExitStack

from bleak import BleakClient
from bleak.exc import BleakError
from bleak.backends.device import BLEDevice

_LOGGER = logging.getLogger(__name__)


class GenericBTDevice:
    """Generic BT Device Class"""
    def __init__(self, ble_device):
        self._ble_device: BLEDevice | None = ble_device
        self._client: BleakClient | None = None
        self._client_stack = AsyncExitStack()
        self._lock = asyncio.Lock()

    async def update(self):
        pass

    async def stop(self):
            pass

    @property
    def connected(self):
        return not self._client is None

    async def get_client(self):
        async with self._lock:
            if not self._client:
                _LOGGER.debug("Connecting")
                try:
                    self._client = await self._client_stack.enter_async_context(BleakClient(self._ble_device, timeout=30))
                except asyncio.TimeoutError as exc:
                    _LOGGER.debug("Timeout on connect", exc_info=True)
                    raise RuntimeError("Timeout on connect") from exc
                except BleakError as exc:
                    _LOGGER.debug("Error on connect", exc_info=True)
                    raise RuntimeError("Error on connect") from exc
            else:
                _LOGGER.debug("Connection reused")

    async def disconnect_client(self):
        async with self._lock:
            if self._client:
                try:
                    await self._client.disconnect()
                    _LOGGER.debug("BLE client disconnected")
                except Exception as e:
                    _LOGGER.debug("Error while disconnecting client: %s", e)
                finally:
                    self._client = None
            else:
                _LOGGER.debug("No active client to disconnect")

    async def write_gatt(self, target_uuid, data, force_reconnect, wake_before_write):

        if force_reconnect:
            await self.disconnect_client()

        if wake_before_write:
            await self.read_gatt(target_uuid)

        await self.get_client()
        uuid_str = "{" + target_uuid + "}"
        uuid = UUID(uuid_str)
        data_as_bytes = bytearray.fromhex(data)
        await self._client.write_gatt_char(uuid, data_as_bytes, True)

    async def read_gatt(self, target_uuid):
        await self.get_client()
        uuid_str = "{" + target_uuid + "}"
        uuid = UUID(uuid_str)
        data = await self._client.read_gatt_char(uuid)
        _LOGGER.debug("Read data: %s", data)
        return data
    async def try_connect(self):
        await self.get_client()
    
    async def disconnect(self):
        async with self._lock:
            if self._client:
                _LOGGER.debug(f"Disconnecting {self._ble_device}")
                await self._client.disconnect()
                _LOGGER.debug(f"Disconnected {self._ble_device}")

                #self.client.unpair()
                self._client = None
            else:
                _LOGGER.debug(f"Already disconnected for {self._ble_device}")


    def update_from_advertisement(self, advertisement):
        pass
