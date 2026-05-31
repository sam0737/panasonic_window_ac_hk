"""nanoeX switch for a Panasonic CW window A/C.

nanoeX is a bit inside the full 27-byte frame, so toggling it re-sends the
current mode/temp/fan/swing. The switch shares the device's assumed state with
the climate entity.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity, RestoredExtraData

from . import PanasonicWindowAcHKConfigEntry
from .device import PanasonicWindowAcHK


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PanasonicWindowAcHKConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the nanoeX switch for this A/C."""
    async_add_entities([PanasonicWindowAcHKNanoexSwitch(entry.runtime_data)])


class PanasonicWindowAcHKNanoexSwitch(SwitchEntity, RestoreEntity):
    """Toggle nanoeX by re-sending the full state frame."""

    _attr_has_entity_name = True
    _attr_translation_key = "nanoex"
    _attr_assumed_state = True
    _attr_icon = "mdi:air-purifier"

    def __init__(self, device: PanasonicWindowAcHK) -> None:
        """Bind to the shared device state."""
        self._device = device
        self._attr_unique_id = f"{device.entry_id}_nanoex"
        self._attr_device_info = device.device_info

    @property
    def extra_restore_state_data(self) -> RestoredExtraData:
        """Snapshot nanoeX so it survives a restart."""
        return RestoredExtraData({"nanoex": self._device.nanoex})

    async def async_added_to_hass(self) -> None:
        """Restore the last nanoeX state (without re-transmitting IR)."""
        await super().async_added_to_hass()
        if (data := await self.async_get_last_extra_data()) is None:
            return
        self._device.nanoex = data.as_dict()["nanoex"]

    @property
    def is_on(self) -> bool:
        """Whether nanoeX is currently assumed on."""
        return self._device.nanoex

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable nanoeX (re-sends the full frame)."""
        self._device.nanoex = True
        await self._device.send_full(self._context)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable nanoeX (re-sends the full frame)."""
        self._device.nanoex = False
        await self._device.send_full(self._context)
        self.async_write_ha_state()
