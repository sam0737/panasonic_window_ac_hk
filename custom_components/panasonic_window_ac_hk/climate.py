"""Climate entity for a Panasonic CW window A/C."""

from __future__ import annotations

from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import PanasonicWindowAcHKConfigEntry
from .const import FAN_MODES, SWING_MODES
from .device import PanasonicWindowAcHK
from .encoder import MAX_TEMP, MIN_TEMP

# Map our operation modes to HA HVAC modes (off is added separately).
_MODE_TO_HVAC = {
    "auto": HVACMode.AUTO,
    "cool": HVACMode.COOL,
    "dry": HVACMode.DRY,
    "heat": HVACMode.HEAT,
}
_HVAC_TO_MODE = {v: k for k, v in _MODE_TO_HVAC.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PanasonicWindowAcHKConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the climate entity for this A/C."""
    async_add_entities([PanasonicWindowAcHKClimate(entry.runtime_data)])


class PanasonicWindowAcHKClimate(ClimateEntity):
    """Optimistic climate control for one A/C (IR is one-way)."""

    _attr_has_entity_name = True
    _attr_name = None  # use the device name
    _attr_icon = "mdi:air-conditioner"
    _attr_assumed_state = True
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = 0.5
    _attr_min_temp = MIN_TEMP
    _attr_max_temp = MAX_TEMP
    _attr_hvac_modes = [
        HVACMode.OFF,
        HVACMode.AUTO,
        HVACMode.COOL,
        HVACMode.DRY,
        HVACMode.HEAT,
    ]
    _attr_fan_modes = FAN_MODES
    _attr_swing_modes = SWING_MODES
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.SWING_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )

    def __init__(self, device: PanasonicWindowAcHK) -> None:
        """Bind to the shared device state."""
        self._device = device
        self._attr_unique_id = f"{device.entry_id}_climate"
        self._attr_device_info = device.device_info

    @property
    def hvac_mode(self) -> HVACMode:
        """Current HVAC mode (OFF when powered off)."""
        if not self._device.power:
            return HVACMode.OFF
        return _MODE_TO_HVAC[self._device.mode]

    @property
    def target_temperature(self) -> float:
        """Current target temperature."""
        return self._device.temp

    @property
    def fan_mode(self) -> str:
        """Current fan mode."""
        return self._device.fan

    @property
    def swing_mode(self) -> str:
        """Current swing mode."""
        return self._device.swing

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set HVAC mode (or power off)."""
        if hvac_mode == HVACMode.OFF:
            self._device.power = False
        else:
            self._device.power = True
            self._device.mode = _HVAC_TO_MODE[hvac_mode]
        await self._device.send_full(self._context)
        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set the target temperature (0.5 C steps)."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        self._device.temp = temperature
        if self._device.power:
            await self._device.send_full(self._context)
        self.async_write_ha_state()

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set the fan speed."""
        self._device.fan = fan_mode
        if self._device.power:
            await self._device.send_full(self._context)
        self.async_write_ha_state()

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        """Set the swing position."""
        self._device.swing = swing_mode
        if self._device.power:
            await self._device.send_full(self._context)
        self.async_write_ha_state()
