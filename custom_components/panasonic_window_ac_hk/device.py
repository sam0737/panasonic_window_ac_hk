"""Shared device object for one Panasonic CW window A/C.

A single ``PanasonicWindowAcHK`` is the source of truth for one physical unit. The
climate entity and the nanoeX switch both mutate this state and re-send a full
frame (nanoeX lives inside the 27-byte frame, so it cannot be toggled without
re-asserting mode/temp/fan/swing). Quiet/Powerful are independent short frames.
"""

from __future__ import annotations

from homeassistant.components import infrared
from homeassistant.core import Context, HomeAssistant
from homeassistant.helpers.entity import DeviceInfo

from .command import PanasonicWindowAcHKCommand
from .const import (
    DEFAULT_FAN,
    DEFAULT_MODE,
    DEFAULT_SWING,
    DEFAULT_TEMP,
    DOMAIN,
)


class PanasonicWindowAcHK:
    """Holds the assumed state for one A/C and sends IR via an emitter."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        name: str,
        emitter_id: str,
    ) -> None:
        """Initialise with the chosen emitter and a default-on state."""
        self._hass = hass
        self.entry_id = entry_id
        self.name = name
        self.emitter_id = emitter_id

        # Assumed state (IR is one-way; we cannot read the unit back).
        self.power = False
        self.mode = DEFAULT_MODE
        self.temp: float = DEFAULT_TEMP
        self.fan = DEFAULT_FAN
        self.swing = DEFAULT_SWING
        self.nanoex = False

    @property
    def device_info(self) -> DeviceInfo:
        """Group all entities of this AC under one HA device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.entry_id)},
            name=self.name,
            manufacturer="Panasonic",
            model="Window-Type A/C (CW-HU/HZ/SU/SUL, HK/Macau)",
        )

    async def _send(self, command: PanasonicWindowAcHKCommand, context: Context | None) -> None:
        await infrared.async_send_command(
            self._hass, self.emitter_id, command, context=context
        )

    async def send_full(self, context: Context | None = None) -> None:
        """Transmit the current full state (or an off frame when powered off)."""
        command = PanasonicWindowAcHKCommand.full(
            off=not self.power,
            mode=self.mode,
            temp=self.temp,
            fan=self.fan,
            swing=self.swing,
            nanoex=self.nanoex,
        )
        await self._send(command, context)

    async def send_short(self, kind: str, context: Context | None = None) -> None:
        """Transmit a Quiet/Powerful toggle (does not change other settings)."""
        await self._send(PanasonicWindowAcHKCommand.short(kind), context)
