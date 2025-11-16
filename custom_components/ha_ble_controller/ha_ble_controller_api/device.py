"""generic bt device"""

from uuid import UUID
import asyncio
import logging
from contextlib import asynccontextmanager

from bleak import BleakClient
from bleak.exc import BleakError
from bleak.backends.device import BLEDevice

_LOGGER = logging.getLogger(__name__)


class GenericBTDevice:
    """Generic BT Device Class"""

    def __init__(self, ble_device):
        self._ble_device: BLEDevice | None = ble_device
        self._client: BleakClient | None = None
        self._lock = asyncio.Lock()

        # Default behaviors for connection management
        self.def_disconnect_before: bool = False
        self.def_disconnect_after: bool = False

    async def update(self):
        pass

    async def stop(self):
        await self.disconnect()

    @property
    def connected(self):
        return self._client is not None

    @asynccontextmanager
    async def get_client(
        self,
        *,
        disconnect_before: bool | None = None,
        disconnect_after: bool | None = None,
    ):
        """
        Async context manager that yields a connected BleakClient.

        Parameters
        ----------
        disconnect_before:
            If True, ensure the client is fully disconnected and reconnected
            before yielding. If False, connect only if not already connected.
            If None, falls back to def_disconnect_before.

        disconnect_after:
            If True, disconnect the client after the context exits.
            If None, falls back to def_disconnect_after.
        """

        if disconnect_before is None:
            disconnect_before = self.def_disconnect_before
        if disconnect_after is None:
            disconnect_after = self.def_disconnect_after

        # Handle the "before" behavior
        if disconnect_before:
            _LOGGER.debug("disconnect_before=True; disconnecting prior to use")
            await self.disconnect()

        # Ensure we have a connected client
        async with self._lock:
            if not self._client:
                _LOGGER.debug("Connecting")
                try:
                    client = BleakClient(self._ble_device, timeout=30)
                    await client.connect()
                    self._client = client
                    _LOGGER.debug("Connected %s", self._ble_device)
                except asyncio.TimeoutError as exc:
                    _LOGGER.debug("Timeout on connect", exc_info=True)
                    raise RuntimeError("Timeout on connect") from exc
                except BleakError as exc:
                    _LOGGER.debug("Error on connect", exc_info=True)
                    raise RuntimeError("Error on connect") from exc
            else:
                _LOGGER.debug("Connection reused for %s", self._ble_device)

            client = self._client

        try:
            yield client
        finally:
            if disconnect_after:
                _LOGGER.debug("disconnect_after=True; disconnecting after use")
                await self.disconnect()

    async def disconnect(self, force: bool = False):
        """
        Disconnect the BLE client.

        Parameters
        ----------
        force:
            Disconnect the client without taking a lock
        """
        if force:
            client = self._client
            self._client = None

            if client:
                try:
                    _LOGGER.debug(
                        "Force disconnecting %s (no lock)", self._ble_device
                    )
                    await client.disconnect()
                    _LOGGER.debug(
                        "Force disconnected %s (no lock)", self._ble_device
                    )
                except Exception as e:  # noqa: BLE001
                    _LOGGER.debug(
                        "Error while force-disconnecting client: %s", e
                    )
            else:
                _LOGGER.debug(
                    "No active client to force-disconnect for %s", self._ble_device
                )
            return

        # Normal, lock-protected path
        async with self._lock:
            if self._client:
                try:
                    _LOGGER.debug("Disconnecting %s", self._ble_device)
                    await self._client.disconnect()
                    _LOGGER.debug("Disconnected %s", self._ble_device)
                except Exception as e:  # noqa: BLE001
                    _LOGGER.debug("Error while disconnecting client: %s", e)
                finally:
                    self._client = None
            else:
                _LOGGER.debug("No active client to disconnect for %s", self._ble_device)

    async def write_gatt(self, target_uuid, data, force_reconnect, wake_before_write):
        if force_reconnect:
            await self.disconnect()

        if wake_before_write:
            await self.read_gatt(target_uuid)

        uuid_str = "{" + target_uuid + "}"
        uuid = UUID(uuid_str)
        data_as_bytes = bytearray.fromhex(data)

        async with self.get_client() as client:
            try:
                await asyncio.wait_for(
                    client.write_gatt_char(uuid, data_as_bytes, True),
                    timeout=30,
                )
            except asyncio.TimeoutError as exc:
                _LOGGER.debug(
                    "Timeout on write_gatt for %s, disconnecting client",
                    self._ble_device,
                    exc_info=True,
                )
                await self.disconnect()
                raise RuntimeError("Timeout on GATT write") from exc

    async def read_gatt(self, target_uuid):
        uuid_str = "{" + target_uuid + "}"
        uuid = UUID(uuid_str)

        async with self.get_client() as client:
            data = await client.read_gatt_char(uuid)

        _LOGGER.debug("Read data: %s", data)
        return data

    async def try_connect(self):
        async with self.get_client():
            pass

    def update_from_advertisement(self, advertisement):
        pass
