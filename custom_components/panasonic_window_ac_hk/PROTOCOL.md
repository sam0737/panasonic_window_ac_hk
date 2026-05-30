# Panasonic Window A/C — Infra‑Red Remote Protocol

A complete, from‑scratch description of the IR protocol used by my Panasonic
window air‑conditioner, reverse‑engineered from Broadlink RF/IR captures. It is
written so that a reader with **no prior knowledge** of Panasonic A/C remotes
can reconstruct a valid signal byte‑for‑byte: carrier, mark/space timing, frame
layout, repetition, checksum, every field, the fixed "magic" bytes, and the
separate short frame used by the **Quiet** and **Powerful** buttons.

---

## 1. Applicable models

The air‑conditioner itself is a **Panasonic** window‑type unit (Hong Kong,
~2023). I think it is a **`CW-HU70ZA`**, but that is from memory — the appliance
model number is **not printed on the unit's outer shell** where I looked, and it
is **not** encoded in the IR signal either, so I can't confirm it from the
capture.

What I _can_ read off the hardware is the **remote control part number:
`ACXA75C20160`** (see §1.1 for what that means). Note the remote part number is
likewise **not present in the IR frame** — the frame only carries Panasonic's
generic model bytes (§7/§9), so the remote number and the appliance number
cannot be derived from each other or from the bytes.

The frame carries Panasonic's generic A/C signature (`02 20 E0 04 …`, see
§7), which is shared across essentially the whole Panasonic A/C line. In
practice this same protocol — possibly minus features such as **nanoeX** on
cooling‑only units — should drive the current Hong Kong window range, e.g. the
models listed at
[Panasonic HK — Window Air‑Conditioner](https://www.panasonic.hk/en/categories/living/ventilation-air-conditioning/window-air-conditioner/).
Units without nanoeX simply ignore the nanoeX bit (§6.6); cooling‑only units
ignore the heat mode value.

### 1.1 Remote part number `ACXA75C20160`

This is a standard Panasonic remote‑control spare‑part number, not an encoding
of any AC capability. It breaks down as:

| Part      | Meaning                                                                                                                          |
| --------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `ACXA75C` | Panasonic's fixed prefix for **A/C infra‑red remote controls** (the `A75C` series).                                              |
| `20160`   | The **specific remote variant** (button layout + IR code set). Just an identifier — it does _not_ decode into mode/feature bits. |

The same remote is commonly written three ways: full part number `ACXA75C20160`,
short `A75C20160`, or just the **`20160`** that is usually printed on the back of
the remote. (Older units sometimes use a `CWA75C…` molding number for the same
thing.) To find a replacement you match this **exact** number, because each one
is tied to a specific group of AC models and a proprietary IR code set
([example listings](https://www.statewideapp.com.au/panasonic-aircon-remote-control-cs-re9mkr-replaces-cwa75c3755-acxa75c21700?Title=Default+Title)).

I could not find a public listing for `ACXA75C20160` specifically, but its
format is genuine and its `201xx` range sits alongside other recent (2020s)
remotes such as `ACXA75C21620` / `ACXA75C21700`, which is consistent with a
~2023 unit. The trailing digits are roughly sequential by release, not a feature
code — so they tell you _which remote_, not _what the protocol does_.

> Everything below is **empirical**, decoded from recorded signals, not taken
> from a datasheet. Where a byte's purpose is unverified it is called out.

---

## 2. Physical layer

| Property    | Value                                                           |
| ----------- | --------------------------------------------------------------- |
| Modulation  | Carrier‑modulated IR, **~38 kHz** carrier                       |
| Line coding | **Pulse distance** (constant mark, data carried in the _space_) |
| Bit order   | **LSB‑first** within each byte                                  |
| Logic       | A "mark" = carrier ON (IR LED pulsing); a "space" = carrier OFF |

### 2.1 Timing (measured, with canonical Panasonic values)

All marks have the same length; the **following space** distinguishes a `0`
from a `1`.

| Element                                   | Measured | Canonical Panasonic |
| ----------------------------------------- | -------- | ------------------- |
| Leader / header **mark**                  | ~3472 µs | 3456 µs             |
| Leader / header **space**                 | ~1766 µs | 1728 µs             |
| Bit **mark** (every bit)                  | ~439 µs  | 432 µs              |
| **`0`** space (after mark)                | ~439 µs  | 432 µs              |
| **`1`** space (after mark)                | ~1278 µs | 1296 µs             |
| **Section gap** (between the two frames)  | ~10.1 ms | 10 000 µs           |
| **Message gap** (trailing, after frame 2) | ~101 ms  | 100 000 µs          |

Decision rule for a receiver: after each ~440 µs mark, measure the space —
**space ≳ 850 µs → `1`, else `0`** (a threshold halfway between 439 and 1278 µs
is robust).

---

## 3. Frame structure & repetition

One button press transmits **one message** made of **two sections (frames)**:

```
[HDR mark][HDR space] [Frame‑1 bits][bit mark]      <- 8 bytes (64 bits)
[10 ms section gap]
[HDR mark][HDR space] [Frame‑2 bits][bit mark]      <- 19 bytes (152 bits)
[100 ms message gap]
```

- Each frame begins with the **header** (3456 µs mark + 1728 µs space).
- Each frame ends with a **single trailing bit mark** (~432 µs) so the last
  space can be measured; the section/message gap follows.
- **Frame 1 = 8 bytes**, **Frame 2 = 19 bytes**, for a **27‑byte (216‑bit)**
  state.
- The message is generally sent **once** per press (no internal repeat); the
  receiver acts on a single well‑formed message. Re‑sending the identical
  message is idempotent for absolute fields (mode/temp/fan/swing) because they
  are absolute, not relative.

The **Quiet/Powerful** buttons are the exception — they send a much shorter
**16‑byte** message (§8).

---

## 4. Bit / byte encoding

Bits are packed **LSB‑first**: the first bit received is bit 0 of the byte, the
eighth bit is bit 7.

```
received bits:  b0 b1 b2 b3 b4 b5 b6 b7
byte value   =  b0 | b1<<1 | b2<<2 | … | b7<<7
```

Example: spaces decoded as `0 1 0 0 0 0 0 0` → byte `0x02`.

---

## 5. Checksum

The **last byte of Frame 2** is a checksum:

```
checksum = ( sum of all Frame‑2 data bytes, excluding the checksum byte ) & 0xFF
```

For the full 27‑byte state that is **`sum(state[8 .. 25]) & 0xFF == state[26]`**
(bytes 8–25 are exactly the 18 data bytes of Frame 2 before the checksum).

The short Quiet/Powerful frame uses the **same rule** over its own shorter
Frame 2: `sum(state[8 .. 14]) & 0xFF == state[15]` (§8).

Frame 1 has **no** checksum (it is a fixed preamble, §7).

---

## 6. Full state frame (27 bytes)

Byte map below was confirmed across **723** captured full frames. "CONST" bytes
are identical in every capture (the reproducible "magic"); "FIELD" bytes carry
settings.

| Byte | Value(s) | Role                                                                                                                                                                       |
| ---: | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
|    0 | `02`     | CONST — Frame‑1 magic                                                                                                                                                      |
|    1 | `20`     | CONST — Frame‑1 magic                                                                                                                                                      |
|    2 | `E0`     | CONST — Frame‑1 magic                                                                                                                                                      |
|    3 | `04`     | CONST — Frame‑1 magic                                                                                                                                                      |
|    4 | `00`     | CONST                                                                                                                                                                      |
|    5 | `00`     | CONST                                                                                                                                                                      |
|    6 | `00`     | CONST                                                                                                                                                                      |
|    7 | `06`     | CONST — end of Frame‑1 magic                                                                                                                                               |
|    8 | `02`     | CONST — Frame‑2 magic (repeats the signature)                                                                                                                              |
|    9 | `20`     | CONST — Frame‑2 magic                                                                                                                                                      |
|   10 | `E0`     | CONST — Frame‑2 magic                                                                                                                                                      |
|   11 | `04`     | CONST — Frame‑2 magic                                                                                                                                                      |
|   12 | `00`     | CONST (full frame). `0x80` marks the **short** toggle frame, §8                                                                                                            |
|   13 | FIELD    | **Power + Mode** (§6.1, §6.2)                                                                                                                                              |
|   14 | FIELD    | **Temperature** (§6.3)                                                                                                                                                     |
|   15 | `80`     | CONST                                                                                                                                                                      |
|   16 | FIELD    | **Fan speed (high nibble) + Swing (low nibble)** (§6.4, §6.5). On this unit the moving louver is **horizontal**; IRremoteESP8266 calls this nibble _vertical_ swing (§6.5) |
|   17 | `0D`     | CONST — IRremoteESP8266's **horizontal‑swing** nibble; our value `0x0D` = its "SwingH Auto" and never changes (§6.5/§9)                                                    |
|   18 | `00`     | CONST                                                                                                                                                                      |
|   19 | `0E`     | CONST — timer field, "disabled" special value                                                                                                                              |
|   20 | `E0`     | CONST — timer field, "disabled" special value                                                                                                                              |
|   21 | `00`     | CONST — Quiet/Powerful bits in the IRremoteESP8266 model; **always 0 here** (we use the short frame instead, §8/§9)                                                        |
|   22 | `00`     | CONST — Ion/filter bit on DKE models; unused here                                                                                                                          |
|   23 | `81`     | CONST — model signature byte (JKE‑family, §9)                                                                                                                              |
|   24 | `00`     | CONST — clock field (window unit has no clock)                                                                                                                             |
|   25 | FIELD    | **Feature byte** — bit `0x04` = **nanoeX** (§6.6)                                                                                                                          |
|   26 | FIELD    | **Checksum** (§5)                                                                                                                                                          |

A known‑good baseline (Auto, 16 °C, fan Auto, swing Auto, nanoeX on):

```
Frame1: 02 20 E0 04 00 00 00 06
Frame2: 02 20 E0 04 00 01 20 80 AF 0D 00 0E E0 00 00 81 00 06 D8
```

### 6.1 Power — byte 13, bit 0

| bit 0 | Meaning |
| ----- | ------- |
| `1`   | On      |
| `0`   | Off     |

"Off" is sent as a normal full frame with bit 0 cleared (e.g. byte 13 = `0x00`).

### 6.2 Mode — byte 13, high nibble (bits 4–7)

| Nibble | Mode |
| -----: | ---- |
|    `0` | Auto |
|    `2` | Dry  |
|    `3` | Cool |
|    `4` | Heat |

So byte 13 = `(modeNibble << 4) | powerBit`. Observed values: `0x00` (off/auto),
`0x01` (auto on), `0x21` (dry on), `0x31` (cool on), `0x41` (heat on).

### 6.3 Temperature — byte 14

```
temperature °C = byte14 / 2           (byte14 = round(°C × 2))
```

Range **16–30 °C** → byte 14 = `0x20`…`0x3C`. In every captured frame the
remote sent **whole degrees**, so byte 14 was always **even** (bit 0 = 0).

But because byte 14 is `°C × 2`, **bit 0 is a 0.5 °C step**, so half-degrees are
representable: e.g. `24.5 °C → round(24.5 × 2) = 0x31`. Whether a given unit
actually acts on the half-degree bit is **untested** — the generated SmartIR
file sets `precision: 0.5` to try it.

### 6.4 Fan speed — byte 16, high nibble (bits 4–7)

| Nibble | Fan         |
| -----: | ----------- |
|    `A` | Auto        |
|    `3` | Low         |
|    `4` | Medium‑Low  |
|    `5` | Medium      |
|    `6` | Medium‑High |
|    `7` | High        |

(Other nibble values are not produced by this remote.)

### 6.5 Swing — byte 16, low nibble (bits 0–3)

On **my** unit (a window A/C) this controls the **horizontal** louver — there is
no separate vertical‑swing feature. The values observed are:

| Nibble | Swing                                 |
| -----: | ------------------------------------- |
|    `F` | Auto (swing on / oscillating)         |
|    `5` | Fixed (vane held at the set position) |

byte 16 = `(fanNibble << 4) | swingNibble`, e.g. `0xAF` = fan Auto + swing Auto;
`0x35` = fan Low + swing Fixed.

**Comparison with IRremoteESP8266 — and why the axis label differs.** In
IRremoteESP8266 this exact nibble (byte 16 low) is **vertical** swing
(`getSwingVertical` / `setSwingVertical`), while **horizontal** swing lives in
**byte 17** low nibble (`getSwingHorizontal`). So the position you control is the
one the library labels _vertical_, **not** horizontal. The names are a
split‑wall‑unit convention (airflow tilted up/down vs panned left/right); a
window unit has a single louver, so what you see as "horizontal" sits in the
byte‑16 slot the library calls "vertical." Mapping the values:

| byte   | nibble         | Your unit            | IRremoteESP8266 constant                                                     |
| ------ | -------------- | -------------------- | ---------------------------------------------------------------------------- |
| 16 low | `F`            | swing on / auto      | `kPanasonicAcSwingVAuto` (`0xF`) — exact match                               |
| 16 low | `5`            | fixed                | `kPanasonicAcSwingVLowest` (`0x5`) — i.e. vane parked at the lowest detent   |
| 17 low | `D` (constant) | unused / always this | `kPanasonicAcSwingHAuto` (`0xD`) — "horizontal swing = auto", left untouched |

So your "fixed" position is, in the library's vocabulary, the **lowest vertical
detent** (`0x5`), and your byte 17 is pinned to the library's **horizontal‑auto**
value (`0xD`) because your remote never drives that second axis. Other
IRremoteESP8266 vertical values you won't see from this remote: Highest `0x1`,
High `0x2`, Middle `0x3`, Low `0x4`.

### 6.6 nanoeX — byte 25, mask `0x04`

| byte 25 & `0x04` | nanoeX |
| ---------------- | ------ |
| set (`0x06`)     | On     |
| clear (`0x02`)   | Off    |

Confirmed by holding everything else constant and toggling only nanoeX: the
**only** changed bit (besides the checksum) was byte 25 `0x04`. The `0x02` bit is
a constant base value for this byte. Cooling‑only / non‑nanoeX units ignore it.

---

## 7. Fixed "magic" bytes (required to reproduce)

These never change and **must** be emitted verbatim or the unit ignores the
frame:

```
Frame‑1 (all 8):   02 20 E0 04 00 00 00 06
Frame‑2 fixed:     bytes 8–12  = 02 20 E0 04 00
                   byte 15     = 80
                   bytes 17–24 = 0D 00 0E E0 00 00 81 00
                   (byte 25 base = 02, plus nanoeX 0x04)
```

`02 20 E0 04` is the Panasonic A/C **manufacturer/protocol signature** and
appears at the start of both frames. Bytes 19–20 (`0E E0`) encode the
"timer disabled" special value, and byte 23 (`81`) is the model signature.

---

## 8. Short frame — Quiet / Powerful toggle

The **Quiet** and **Powerful** buttons do **not** send the full state. They send
a dedicated **16‑byte** message: the normal 8‑byte Frame 1, then a **shortened
8‑byte Frame 2**. Captured bytes:

```
Quiet:     02 20 E0 04 00 00 00 06 | 02 20 E0 04 80 81 33 3A
Powerful:  02 20 E0 04 00 00 00 06 | 02 20 E0 04 80 86 35 41
                                     ^^^^^^^^^^^ ^^^^^^^^ ^^
                                     magic       payload  cksum
```

| Byte | Quiet         | Powerful      | Role                                               |
| ---: | ------------- | ------------- | -------------------------------------------------- |
| 8–11 | `02 20 E0 04` | `02 20 E0 04` | Frame‑2 magic (same signature)                     |
|   12 | `80`          | `80`          | short‑frame marker (`0x80`; full frame has `0x00`) |
|   13 | `81`          | `86`          | command payload                                    |
|   14 | `33`          | `35`          | command payload                                    |
|   15 | `3A`          | `41`          | **checksum** = `sum(bytes 8–14) & 0xFF`            |

Both verified: `sum(02+20+E0+04+80+81+33)&0xFF = 0x3A` ✓ and
`sum(02+20+E0+04+80+86+35)&0xFF = 0x41` ✓ — i.e. **the same checksum rule as the
full frame**, just over the shorter body.

**Why these behave as pure toggles.** The frame is physically too short to
contain the mode/temperature/fan/swing/nanoeX fields (those live at bytes
13/14/16/25 of the _19‑byte_ Frame 2, which is absent here). So the message says
only "toggle Quiet" / "toggle Powerful" and the unit keeps whatever it was
already running. This matches the observed behaviour: pressing Quiet/Powerful
changes nothing else. It is **not** that the A/C "ignores" other fields when a
bit is set — there simply are no other fields in this frame.

To reproduce, **replay these two captures verbatim**; do not synthesise them
from a full‑state encoder.

---

## 9. Comparison with IRremoteESP8266

[IRremoteESP8266](https://github.com/crankyoldgit/IRremoteESP8266)
(`ir_Panasonic.cpp` / `.h`) is the de‑facto reference for Panasonic A/C IR. Our
unit **is** that protocol — same carrier, same timings, same 27‑byte
LSB‑first state, same checksum (`sum(state[8..25]) & 0xFF`), same `02 20 E0 04`
signature and the same `kPanasonicAcSection1 = {02,20,E0,04,00,00,00,06}`
preamble. Differences are in a few model bytes and in how features are sent.

### 9.1 Magic / signature bytes

|     Byte | Ours                      | IRremoteESP8266 meaning                                         | Notes                                                                                                |
| -------: | ------------------------- | --------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
|      0–7 | `02 20 E0 04 00 00 00 06` | Section‑1 constant                                              | **Exact match**                                                                                      |
|     8–11 | `02 20 E0 04`             | Section‑2 signature                                             | **Exact match**                                                                                      |
|       15 | `80`                      | constant in known‑good state                                    | match                                                                                                |
| 16 (low) | `F`/`5`                   | **vertical** swing nibble (`getSwingVertical`)                  | our physical louver is horizontal but lives in this slot; `F`=SwingVAuto, `5`=SwingVLowest (§6.5)    |
|       17 | `0D`                      | **horizontal** swing nibble (`getSwingHorizontal`)              | our value `0x0D` = `kPanasonicAcSwingHAuto`; pinned, never driven (window unit has one louver, §6.5) |
|    19–20 | `0E E0`                   | off‑timer field                                                 | encodes the **"timer disabled" special value** (`0x600`)                                             |
|       21 | `00`                      | **Quiet (bit 0) / Powerful (bit 5)**                            | we never set these here — see §9.3                                                                   |
|       22 | `00`                      | **Ion / filter (bit 0)**, DKE only                              | unused on our unit                                                                                   |
|       23 | `81`                      | **model signature**                                             | `& 0x80` set ⇒ **JKE‑family**                                                                        |
|       25 | `02`/`06`                 | clock byte in the library; **`0x06` is the DKE reset constant** | we repurpose bit `0x04` as **nanoeX**                                                                |

### 9.2 Closest model

By signature bytes our unit is a **hybrid**:

- **byte 23 = `0x81`** (the `0x80` bit) is IRremoteESP8266's **JKE** marker.
  Its JKE detection additionally expects **byte 17 == `0x00`**, but ours is
  `0x0D`, so the library would classify it as **unknown** while still decoding
  every standard field correctly.
- **byte 25 defaulting to `0x06`** matches the library's **DKE** reset constant
  (`stateReset()` sets `remote_state[25] = 0x06` for `kPanasonicDke`).

**Closest enumerated model: JKE** (with a DKE‑like feature byte). For sending,
treat it as generic Panasonic A/C and preserve our exact constant bytes rather
than relying on a specific model preset.

### 9.3 Feature handling differs (important)

- **nanoeX**: IRremoteESP8266 has **no concept of nanoeX**. It treats byte 25 as
  a fixed model byte (`0x00`, or `0x06` for DKE) and never toggles it. Our
  empirical finding — **byte 25 bit `0x04` = nanoeX** — is beyond what the
  library models. A library‑generated frame would not carry/toggle nanoeX.
- **Quiet / Powerful**: IRremoteESP8266 encodes these as **bits in the full
  27‑byte frame** — `kPanasonicAcQuietOffset = 0` and
  `kPanasonicAcPowerfulOffset = 5`, both in **byte 21** (mutually exclusive).
  Our remote instead sends the **short 16‑byte toggle frame** (§8) and leaves
  byte 21 = `0x00` in every full frame. Consequence: driving the unit through an
  IRremoteESP8266‑style encoder would re‑transmit the whole state (re‑asserting
  mode/temp/fan/swing) to flip Quiet/Powerful — the opposite of our remote's
  minimal toggle.

---

## 10. End‑to‑end reconstruction recipe

To build, say, **Cool, 24 °C, fan High, swing Auto, nanoeX on**:

1. **Frame 1** (fixed): `02 20 E0 04 00 00 00 06`.
2. **Frame 2 bytes 8–25**, starting from the constants and filling fields:
   - 8–12: `02 20 E0 04 00`
   - 13: mode Cool (`3`) + power on (`1`) → `0x31`
   - 14: 24 °C × 2 → `0x30` (a half-degree such as 24.5 °C → `round(24.5 × 2)` = `0x31`)
   - 15: `80`
   - 16: fan High (`7`) + swing Auto (`F`) → `0x7F`
   - 17–24: `0D 00 0E E0 00 00 81 00`
   - 25: base `0x02` + nanoeX `0x04` → `0x06`
3. **Checksum** byte 26 = `sum(bytes 8..25) & 0xFF`.
4. **Transmit**: header → Frame 1 bits (LSB‑first, pulse‑distance) → trailing bit
   mark → **10 ms gap** → header → Frame 2 bits → trailing bit mark → **100 ms
   gap**. Each bit = ~432 µs mark + (432 µs for `0` / 1296 µs for `1`) space.

For **Quiet/Powerful**, skip all of this and replay the captured 16‑byte frame
from §8 verbatim.

---

## 11. Broadlink capture notes (for replay tooling)

The raw captures are Broadlink IR packets, Base64‑encoded:

- Byte 0 = `0x26` (IR), byte 1 = repeat count, bytes 2–3 = payload length
  (**little‑endian**).
- Payload = pulse durations in Broadlink ticks, converted with
  `µs = ticks × 8192 / 269` (**1 tick ≈ 30.46 µs**).
- A duration > 255 ticks is encoded as `0x00` followed by a **big‑endian**
  uint16 (note: the length header is little‑endian, but these extension values
  are big‑endian — easy to get wrong, and it only affects the long gap values,
  not the bit timings).
- Packet ends with the standard `0x0D 0x05` trailer / padding.

Demodulation: strip the wrapper, split on the ~10 ms section gap into Frame 1 /
Frame 2, take every (mark, space) pair, map space>threshold→`1`, pack LSB‑first.
