# Panasonic Window-Type Air Conditioner (Hong Kong / Macau) — Home Assistant integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

A custom Home Assistant integration that controls Panasonic **window /
through-the-wall air conditioners sold in Hong Kong and Macau** over infrared,
using Home Assistant's native **`infrared`** platform (HA 2026.4+). Instead of
shipping precomputed Base64 blobs, it encodes the reverse-engineered Panasonic
protocol into protocol-agnostic microsecond timings and lets any configured IR
emitter (Broadlink, ESPHome IR proxy, etc.) transmit them.

## Scope / supported models

The **CW-HU / CW-HZ / CW-SU / CW-SUL** families are (as far as I can tell) the
Hong Kong / Macau window-AC line-up. This integration was **reverse-engineered
and verified on a single `CW-HU70ZA`**. Other models in those families that use
the **same IR remote / protocol** should work, but this is **not** guaranteed
for every `CW-*` model — Panasonic uses the `CW` prefix for other markets and
product variants too, which may use a different IR protocol. If a model does not
respond, its codes will need to be re-captured.

It exposes, per A/C, a single HA **device** with:

- a **climate** entity — power, modes (auto/cool/dry/heat), target temperature
  (16–30 °C in **0.5 °C** steps), fan speed (auto/low/mediumLow/medium/
  mediumHigh/high), and swing (auto/fixed);
- a **nanoeX switch**;
- **Quiet** and **Powerful** buttons (momentary toggles).

> Protocol details: see [`PROTOCOL.md`](custom_components/panasonic_window_ac_hk/PROTOCOL.md)
> in the integration folder.

## Requirements

- Home Assistant **2026.4 or later** (the release that added the native
  `infrared` platform).
- At least one **infrared emitter** entity (`infrared.*`). This integration does
  not talk to IR hardware directly — it sends commands through an emitter you
  already have (e.g. a Broadlink blaster or an ESPHome IR proxy).

## Install

### Via HACS (recommended)

1. In HACS, open the menu (top right) → **Custom repositories**.
2. Add `https://github.com/sam0737/panasonic_window_ac_hk` with category
   **Integration**.
3. Search HACS for **Panasonic Window-Type Air Conditioner** and download it.
4. **Restart** Home Assistant.

### Manual

1. Copy the integration folder into your Home Assistant config directory:

   ```
   <config>/custom_components/panasonic_window_ac_hk/
   ```

   (Copy the whole `custom_components/panasonic_window_ac_hk/` folder from this repo.)
2. **Restart** Home Assistant.

## Configure (one entry per A/C)

Setup is entirely through the UI — no YAML.

1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **"Panasonic"** or **"Window"** (full title: *Panasonic
   Window-Type Air Conditioner (Hong Kong / Macau)*).
3. In the form, enter a **Name** and pick the **Infrared emitter** for that room.
4. Repeat for each A/C.

If the wizard aborts with *"No infrared emitters were found"*, set up an IR
blaster first (so an `infrared.*` entity exists), then retry.

### Example: 3 rooms / 3 blasters

| Name             | Infrared emitter   |
| ---------------- | ------------------ |
| `細房 AC`        | `infrared.small`   |
| `大房 AC`        | `infrared.master`  |
| `多用途房 AC`    | `infrared.multi`   |

Each entry produces one device with:

- `climate.<name>`
- `switch.<name>_nanoex`
- `button.<name>_quiet`, `button.<name>_powerful`

The UI is localized; with the profile language set to 繁體中文, the nanoeX /
Quiet / Powerful labels and the setup dialog appear in Traditional Chinese.

## Test it

1. Point the chosen blaster at the A/C.
2. On the climate card: turn on, set a mode, nudge the temperature (0.5 °C
   steps), change fan/swing — the A/C should respond.
3. Toggle the **nanoeX** switch (re-sends the full state with the nanoeX bit).
4. Press **Quiet** / **Powerful** (short toggle frames).

State is **assumed** — IR is one-way, so Home Assistant shows the last commanded
state, not a reading from the unit.

## Notes & caveats

- **0.5 °C** steps: the protocol encodes temperature as `°C × 2` (byte 14), so
  half degrees are representable. Whether your specific unit *acts* on the
  half-degree bit is untested; if it rounds, set whole degrees.
- **nanoeX** is part of the full frame, so toggling it re-asserts the current
  mode/temp/fan/swing (by design).
- **Quiet/Powerful** are momentary toggles on the unit; the buttons just fire
  the dedicated short frames and keep no state.
- Iterating on the code: use **Reload** on the integration entry (or restart
  HA). Config entries persist across restarts.

## Verify the encoder (developers)

The encoder is pure Python (no HA dependency) and is round-trip tested against
its own demodulator:

```
python -m pytest tests/ -q
```

This sweeps every mode × fan × swing × nanoeX × 0.5 °C temperature plus the
off frame and both short frames, decoding each generated timing list back to
bytes and checking the checksum.

## License

[MIT](LICENSE) © 2026 Sam Wong.
