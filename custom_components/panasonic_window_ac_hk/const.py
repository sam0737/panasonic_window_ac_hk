"""Constants for the Panasonic CW window A/C integration."""

from __future__ import annotations

DOMAIN = "panasonic_window_ac_hk"

CONF_NAME = "name"
CONF_EMITTER = "emitter"

# Default semantic state for a freshly added unit.
DEFAULT_MODE = "cool"
DEFAULT_TEMP = 24.0
DEFAULT_FAN = "auto"
DEFAULT_SWING = "auto"

# HVAC operation modes exposed by the climate entity (must be valid HA modes).
OPERATION_MODES = ["auto", "cool", "dry", "heat"]
# Fan speeds (matches the encoder's FAN_NIBBLE keys).
FAN_MODES = ["auto", "low", "mediumLow", "medium", "mediumHigh", "high"]
# Swing positions (matches the encoder's SWING_NIBBLE keys).
SWING_MODES = ["auto", "fixed"]
