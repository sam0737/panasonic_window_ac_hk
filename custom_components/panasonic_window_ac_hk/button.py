"""Quiet / Powerful toggle buttons for a Panasonic CW window A/C.

These send the dedicated 16-byte short frames. They are momentary toggles on the
unit and carry no mode/temp/fan/swing, so they are stateless buttons rather than
part of the climate entity.
"""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import PanasonicWindowAcHKConfigEntry
from .device import PanasonicWindowAcHK


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PanasonicWindowAcHKConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Quiet and Powerful buttons for this A/C."""
    device = entry.runtime_data
    async_add_entities(
        [
            PanasonicWindowAcHKToggleButton(device, "quiet", "mdi:volume-mute"),
            PanasonicWindowAcHKToggleButton(device, "powerful", "mdi:rocket-launch"),
        ]
    )


class PanasonicWindowAcHKToggleButton(ButtonEntity):
    """A momentary Quiet/Powerful toggle (short frame)."""

    _attr_has_entity_name = True

    def __init__(
        self,
        device: PanasonicWindowAcHK,
        kind: str,
        icon: str,
    ) -> None:
        """Bind to the device and the short-frame kind to send."""
        self._device = device
        self._kind = kind
        self._attr_translation_key = kind
        self._attr_icon = icon
        self._attr_unique_id = f"{device.entry_id}_{kind}"
        self._attr_device_info = device.device_info

    async def async_press(self) -> None:
        """Send the Quiet/Powerful toggle frame."""
        await self._device.send_short(self._kind, self._context)
