"""Hardware-free verification of the Panasonic window A/C encoder.

Round-trip check: every generated frame is demodulated straight back from its
microsecond timings and compared to the semantic inputs, and the checksum is
recomputed. No Home Assistant or IR hardware required -- just ``pytest``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Import the encoder directly from the integration package without needing HA.
_PKG = Path(__file__).resolve().parent.parent / "custom_components" / "panasonic_window_ac_hk"
sys.path.insert(0, str(_PKG))

import encoder  # noqa: E402  (path injected above)

# Demod thresholds in microseconds: a data space is 432 (0) or 1296 (1);
# inter-frame gaps are 10000 / 100000.
SPACE_THRESHOLD = 850
GAP_THRESHOLD = 3000

MODE_BY_NIBBLE = {0x0: "auto", 0x2: "dry", 0x3: "cool", 0x4: "heat"}
FAN_BY_NIBBLE = {
    0xA: "auto",
    0x3: "low",
    0x4: "mediumLow",
    0x5: "medium",
    0x6: "mediumHigh",
    0x7: "high",
}
SWING_BY_NIBBLE = {0xF: "auto", 0x5: "fixed"}

OPERATION_MODES = ["auto", "cool", "dry", "heat"]
FAN_MODES = ["auto", "low", "mediumLow", "medium", "mediumHigh", "high"]
SWING_MODES = ["auto", "fixed"]


def timings_to_bytes(timings: list[int]) -> list[int]:
    """Inverse of ``encoder.frame_to_timings``: signed timings -> state bytes."""
    out: list[int] = []
    i = 0
    n = len(timings)
    while i < n:
        i += 2  # skip header mark + space
        bits: list[int] = []
        while i + 1 < n:
            space = -timings[i + 1]  # spaces are stored negative
            if space > GAP_THRESHOLD:  # trailing mark + inter-frame/message gap
                i += 2
                break
            bits.append(1 if space > SPACE_THRESHOLD else 0)
            i += 2
        for b in range(0, len(bits) - 7, 8):
            byte = 0
            for j in range(8):
                byte |= bits[b + j] << j
            out.append(byte)
    return out


def half_degrees() -> list[float]:
    """All 0.5 C steps from MIN_TEMP to MAX_TEMP inclusive."""
    return [h / 2 for h in range(encoder.MIN_TEMP * 2, encoder.MAX_TEMP * 2 + 1)]


def decode_full(state: list[int]) -> dict:
    """Decode a 27-byte state into semantic fields."""
    return {
        "off": (state[13] & 0x01) == 0,
        "mode": MODE_BY_NIBBLE[state[13] >> 4],
        "temp": state[14] / 2,
        "fan": FAN_BY_NIBBLE[state[16] >> 4],
        "swing": SWING_BY_NIBBLE[state[16] & 0x0F],
        "nanoex": (state[encoder.NANOEX_BYTE] & encoder.NANOEX_MASK) != 0,
        "checksum_ok": len(state) == 27
        and encoder.checksum(state, 8, 25) == state[26],
    }


@pytest.mark.parametrize("mode", OPERATION_MODES)
@pytest.mark.parametrize("fan", FAN_MODES)
@pytest.mark.parametrize("swing", SWING_MODES)
@pytest.mark.parametrize("nanoex", [False, True])
def test_full_frame_round_trip(mode, fan, swing, nanoex):
    """Every mode x fan x swing x nanoex x 0.5C temp round-trips exactly."""
    for temp in half_degrees():
        state = encoder.build_full_frame(
            mode=mode, temp=temp, fan=fan, swing=swing, nanoex=nanoex
        )
        assert state[26] == encoder.checksum(state, 8, 25)

        decoded = decode_full(timings_to_bytes(encoder.frame_to_timings(state)))
        assert decoded["checksum_ok"], (mode, fan, swing, nanoex, temp)
        assert not decoded["off"]
        assert decoded["mode"] == mode
        assert decoded["temp"] == temp
        assert decoded["fan"] == fan
        assert decoded["swing"] == swing
        assert decoded["nanoex"] == nanoex


def test_off_frame():
    """The off frame clears the power bit and keeps a valid checksum."""
    state = encoder.build_full_frame(
        off=True, mode="auto", temp=encoder.MIN_TEMP, fan="auto", swing="auto", nanoex=False
    )
    decoded = decode_full(timings_to_bytes(encoder.frame_to_timings(state)))
    assert decoded["off"]
    assert decoded["checksum_ok"]


@pytest.mark.parametrize(
    ("kind", "expected"),
    [
        ("quiet", [0x02, 0x20, 0xE0, 0x04, 0x00, 0x00, 0x00, 0x06,
                   0x02, 0x20, 0xE0, 0x04, 0x80, 0x81, 0x33, 0x3A]),
        ("powerful", [0x02, 0x20, 0xE0, 0x04, 0x00, 0x00, 0x00, 0x06,
                      0x02, 0x20, 0xE0, 0x04, 0x80, 0x86, 0x35, 0x41]),
    ],
)
def test_short_frame(kind, expected):
    """Quiet/Powerful short frames match captured bytes and checksum."""
    state = encoder.build_short_frame(kind)
    assert state == expected
    assert encoder.checksum(state, 8, 14) == state[15]
    assert timings_to_bytes(encoder.frame_to_timings(state)) == expected


def test_half_degree_encoding():
    """24.5 C maps to byte 14 = 0x31 (round(24.5 * 2))."""
    state = encoder.build_full_frame(
        mode="cool", temp=24.5, fan="high", swing="auto", nanoex=True
    )
    assert state[14] == 0x31
