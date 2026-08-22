# Movement / Animation Studio — Planning Notes

Working notes from a planning discussion about building a movement studio for
Sesame: a way to test and play with movement, explore more organic/fluid
quadruped motion (inspired by how the bots in Arc Raiders move), and make it
easier to create new commands without a firmware reflash each time.

This is a planning doc, not an implementation — no studio code exists yet.

---

## Goal

- A sandbox for composing and testing new movement commands quickly (fun,
  iterative — no reflash cycle).
- Explore animation principles to make Sesame's gait and poses feel more
  organic/fluid rather than mechanical.
- Support both USB (tethered, direct serial) and the existing WiFi/HTTP API
  as connection options.

---

## Current System (as of this planning pass)

Everything lives in two firmware files + one disconnected desktop tool. No
IK, no software interpolation, no keyframe file format — servos snap to
hardcoded target angles.

- **`firmware/movement-sequences.h`** — all poses/gaits (`stand`, `rest`,
  `wave`, `dance`, `swim`, `point`, `pushup`, `bow`, `cute`, `freaky`,
  `worm`, `shake`, `shrug`, `dead`, `crab`, plus `forward`/`backward`/
  `left`/`right` gaits) as flat sequences of `setServoAngle()` calls with
  `delayWithFace()` waits in between. Servo enum: `R1/R2/L1/L2` = shoulders,
  `R3/R4/L3/L4` = knees (2 DOF per leg × 4 legs = 8 servos).
- **`firmware/sesame-firmware-main.ino`**:
  - `setServoAngle()` (~line 771) — writes the servo, then always blocks for
    `motorCurrentDelay` ms.
  - Serial CLI (from ~line 517) already supports live control with **no
    firmware changes needed**:
    - `"<motorNum> <angle>\n"` — set one servo (e.g. `"3 90"`)
    - `"all <angle>\n"` — set all 8 to the same angle
    - `subtrim`, `subtrim save`, `subtrim reset`, `subtrim <n> <v>` — per-servo
      trim
  - HTTP/JSON API: `/cmd?go=`, `/cmd?pose=`, `/api/command`,
    `/api/settings` (GET returns `frameDelay`, `walkCycles`,
    `motorCurrentDelay`, `faceFps`; same keys settable via query args on
    `handleSetSettings`, ~line 254–260) — **`motorCurrentDelay` is already
    runtime-tunable over WiFi, no reflash required.**
  - Tuning globals: `frameDelay` (100ms, gait step spacing), `walkCycles`
    (10, iterations per walk call), `motorCurrentDelay` (20ms, see below).
- **`software/sesame-studio/sesame_studio.py`** — Tkinter desktop tool.
  Shows a top-down schematic with 8 angle input boxes, lets you type angles
  and "+ Add Frame" to generate `setServoAngle()` C++ lines, then copy to
  clipboard for pasting into the Arduino IDE. **No live robot connection, no
  playback/preview, no save/load, no IK.** Pure code generator.

---

## Key Constraint: `motorCurrentDelay` is a safety limit, not a taste setting

`sesame-firmware-main.ino:105`:
```cpp
int motorCurrentDelay = 20; // ms delay between motor movements to prevent over-current
```

This is enforced *inside* `setServoAngle()` itself, so **every** servo write
— from gaits, poses, the web UI, or the serial CLI — is automatically
spaced by this delay. It's there to stop multiple MG90S servos from all
drawing large correction current simultaneously and browning out the shared
5V rail.

Supporting evidence from the hardware docs:
- BOM (`hardware/bom/README.md`): Sesame needs "at least 5V at 3A available
  at the rails," powered via buck converter + battery or USB-C PD when
  tethered, with a 1000µF cap smoothing the buck converter output.
- Wiring guide (`docs/wiring-guide/README.md`): Distro Board V1 "cannot run
  on tethered USB-C power," and V2 has known "battery brownouts." Headroom
  is already known to be tight on some builds.

**Implication for studio design:** don't fight this constraint with dense
per-frame micro-stepping (streaming many tiny angle increments to fake
smooth interpolation) — that multiplies command count and either gets
rate-limited into uselessness, or tempts shrinking the delay carelessly.

**Reframe:** real animal/robot gaits don't move all joints simultaneously
either — motion is naturally staggered (one joint leads, others follow a
beat later; diagonal leg pairs; follow-through). So the studio should
schedule sparse, eased keyframes per joint with individual timing offsets,
respecting the existing per-command safety delay, and let the servo's own
mechanical slew provide the in-between smoothness. This treats the
current-limiting requirement as compatible with — not opposed to — the
animation goal of overlapping/staggered action.

### Testing smaller delay values

`motorCurrentDelay` is already adjustable at runtime via
`/api/settings?motorCurrentDelay=<ms>` — no firmware change needed to
experiment. Proposed protocol for testing lower values on real hardware
(to be done on the physical robot, not from this remote session — no USB
access here):

1. Step the value down in small increments (e.g. 20 → 15 → 10 → 7 → 5ms).
2. At each step, run a worst-case move (all 8 servos, large angle deltas at
   once — e.g. `all 0` then `all 180`).
3. Watch for brownout signs: ESP32 reboot (garbage on serial monitor, boot
   messages reappearing), OLED flicker/reinit, WiFi dropping, servo
   chatter/stall. Ideally also watch the 5V rail with a meter, since a sag
   can happen without a full reset.
4. Back off one step as soon as any symptom appears; that's the safe floor
   for that specific robot's power setup (will vary by battery vs. USB-C
   tethered, buck converter quality, wiring gauge, etc.).

---

## Animation Principles to Bring In (Arc-Raiders-style fluidity)

1. **Easing** — ease-in/ease-out instead of the current linear snap-to-angle.
   Biggest single perceptual win.
2. **Overlapping action / staggered timing** — joints don't start/stop in
   sync; a "wave" through hip → knee → foot. Also the piece that keeps us
   inside the current budget (see above).
3. **Body arc, not fixed-height stepping** — a subtle sinusoidal body
   bob/rise-and-fall as diagonal pairs push off/land, instead of a flat
   walking height.
4. **Anticipation** — a small opposite-direction micro-move before a big
   action (e.g. weight-shift before lifting a leg) reads as intentional
   rather than mechanical.
5. **Gait phase offset** — vary diagonal-pair timing (0.5 = pure trot phase
   offset vs. 0.25 = walk) for different character at the same speed.
6. **Follow-through** — slight overshoot-and-settle when stopping, instead
   of a hard stop.

---

## Proposed Studio Architecture (direction, not yet built)

- **Connection:** USB serial to start (already works today via the existing
  `"<n> <a>"` / `"all <a>"` CLI, zero firmware changes). WiFi/HTTP API as a
  secondary/parallel option later.
- **Motion model:** per-joint keyframe list (angle + arrival time + easing
  curve), not dense per-frame streaming. A scheduler walks the combined
  8-joint timeline and fires single serial commands at the right moments,
  naturally staggering joints in time.
- **Movement files:** poses/gaits saved as data (e.g. JSON) separate from
  firmware — compose, save, replay, remix without touching C++.
- **Export path:** once a move feels right, generate the equivalent
  `setServoAngle()` C++ block (similar to what `sesame_studio.py` already
  does) to graduate it into a permanent named command in
  `movement-sequences.h`.
- **UI stack:** undecided — options discussed were (a) a local web app
  (Python backend + browser UI, better for curve/timeline editing), (b)
  extending the existing Tkinter tool, (c) a plain script first to validate
  the serial protocol and current-safety findings before investing in UI.
  Given the hardware-safety unknowns above, leaning toward (c) as the
  starting point.

---

## Open Questions / Decisions Needed

- [ ] What's the actual safe floor for `motorCurrentDelay` on the specific
      build (battery vs. tethered, which distro board revision)? Needs
      physical testing per the protocol above.
- [ ] UI stack for the studio (web app vs. Tkinter extension vs. script-first).
- [ ] Whether gait phase-offset / body-bob parameters should live in the
      studio only, or eventually become new tunable firmware globals
      (like `frameDelay`/`walkCycles` today).
- [ ] How movement files (keyframe JSON) should be structured/named/versioned.

---

## Next Steps

1. Validate the current-safety findings and serial protocol on real
   hardware (MacBook + USB, per the test protocol above).
2. Decide UI stack once the underlying motion-scheduling approach is
   validated.
3. Prototype the staggered-keyframe scheduler against 1–2 joints before
   scaling to a full gait.

*No studio code has been written yet — this doc reflects planning
discussion only.*
