"""Panasonic window A/C integration for Hong Kong / Macau models.

Covers the CW-HU / CW-HZ / CW-SU / CW-SUL families (verified on CW-HU70ZA);
drives them via Home Assistant's native infrared platform.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import CONF_EMITTER, CONF_NAME, DOMAIN

if TYPE_CHECKING:
    from .device import PanasonicWindowAcHK

PLATFORMS: list[Platform] = [Platform.CLIMATE, Platform.SWITCH, Platform.BUTTON]

# Forward reference (string) so importing this package - e.g. when Home
# Assistant loads the config flow - does NOT pull in device.py -> command.py ->
# infrared_protocols. Those are only needed once an entry is set up.
PanasonicWindowAcHKConfigEntry = ConfigEntry["PanasonicWindowAcHK"]


async def async_setup_entry(
    hass: HomeAssistant, entry: PanasonicWindowAcHKConfigEntry
) -> bool:
    """Set up one A/C from a config entry."""
    # Imported lazily so config-flow registration never depends on the encoder
    # or the infrared_protocols library being importable.
    from .device import PanasonicWindowAcHK

    device = PanasonicWindowAcHK(
        hass,
        entry_id=entry.entry_id,
        name=entry.data[CONF_NAME],
        emitter_id=entry.data[CONF_EMITTER],
    )
    entry.runtime_data = device
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = device

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: PanasonicWindowAcHKConfigEntry
) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
