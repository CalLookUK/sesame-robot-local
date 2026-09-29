# Otto Bot Hardware Wiring Reference

ESP32-S3 Mini based Otto bot. Covers power architecture and all GPIO/pin assignments agreed on so far.

## Bill of materials (electronics)

- ESP32-S3 Mini dev board
- PCA9685 16-channel PWM/servo driver
- 4x MF90 micro metal-gear servos
- Arduino LED Matrix (ABX00152)
- INMP441 I2S digital microphone
- MAX98357A I2S class-D amplifier
- HC-SR04 ultrasonic distance sensor (standard 5V version)
- 3.7V 2600mAh Li-ion battery, with protection PCB
- MT3608 step-up (battery -> 5V, servo rail)
- 2nd step-up/buck module (battery -> 5V, logic/audio rail)

## Power architecture

Two independent 5V rails off the same battery, in parallel (not in series), sharing one common ground.

### Rail A - servo power

```
Battery + -> MT3608 IN+
Battery - -> MT3608 IN-
MT3608 OUT+ -> PCA9685 V+
MT3608 OUT- -> PCA9685 GND
```

- Add a 470-1000uF bulk capacitor across PCA9685 V+/GND to absorb servo current spikes.
- Nothing else connects to this rail - servos only.
- MT3608 is current-limited (~1.2-1.5A continuous realistic) - avoid commanding all 4 servos to stall simultaneously; stagger movements in firmware.

### Rail B - logic/audio power

```
Battery + -> Step-up #2 IN+
Battery - -> Step-up #2 IN-
Step-up #2 OUT+ -> power distribution header (+ row)
Step-up #2 OUT- -> power distribution header (- row)
```

Devices powered from Rail B:
- ESP32-S3 (5V/VIN pin)
- LED Matrix (VCC)
- INMP441 (VDD)
- MAX98357A (VIN)
- HC-SR04 (VCC)

### Common ground

Rail A GND, Rail B GND, battery GND, and all device GNDs tie together at one star-ground point.

### Pre-power checklist

- Verify both step-up outputs read 5.0V unloaded with a multimeter before connecting anything.
- Confirm Rail A and Rail B are never bridged.
- Confirm INMP441 L/R pin is tied to GND (not floating).
- Confirm MAX98357A SD pin is floating (not accidentally grounded).

## GPIO / signal map (ESP32-S3)

### I2C bus - shared by PCA9685 + LED Matrix

| Signal | GPIO |
|---|---|
| SDA | GPIO8 |
| SCL | GPIO9 |

Both devices' SDA wires join at GPIO8, both SCL wires join at GPIO9 (single shared bus, daisy-chained or Y-split). Distinguished by I2C address - PCA9685 defaults to 0x40; confirm LED Matrix address doesn't collide.

### I2S - microphone input (I2S0)

| INMP441 pin | ESP32-S3 GPIO |
|---|---|
| WS | GPIO4 |
| SCK | GPIO5 |
| SD | GPIO6 |
| L/R | GND (selects left channel) |

### I2S - amplifier output (I2S1)

| MAX98357A pin | ESP32-S3 GPIO |
|---|---|
| LRC | GPIO15 |
| BCLK | GPIO16 |
| DIN | GPIO17 |
| SD | float (leave unconnected) |

Mic and amp use separate I2S peripherals (I2S0 vs I2S1) - not sharing clocks, for simplicity.

### Ultrasonic sensor (HC-SR04, standard 5V version)

| HC-SR04 pin | ESP32-S3 GPIO |
|---|---|
| Trig | GPIO18 (direct) |
| Echo | GPIO12 (via voltage divider) |

Echo divider (5V -> ~3.3V):

```
HC-SR04 Echo --[1k ohm]--+--[2k ohm]-- GND
                          |
                       GPIO12
```

Powered from Rail B (5V) - do not run at 3.3V, this is the standard (non-P) variant and needs 5V for reliable trigger timing/range.

### Servo channels (PCA9685)

| Servo | PCA9685 channel |
|---|---|
| Left leg | 0 |
| Right leg | 1 |
| Left foot | 2 |
| Right foot | 3 |

Adjust to match physical assembly and firmware config.

## Reserved / avoid

- GPIO0, 3, 45, 46 - strapping pins, avoid using for peripherals (can affect boot).
- GPIO19/20 - native USB D-/D+ on many S3 boards, avoid if using USB.
- GPIO43/44 - UART0 TX/RX.

## Notes / gotchas

- Arduino LED Matrix (ABX00152) also breaks out SWCLK/SWDIO/PF2 debug pins - not needed for normal operation, leave disconnected.
- Keep I2S mic wiring short and away from servo/boost-converter wiring - sensitive to switching noise.
- If using 2.54mm headers for Rail B distribution, prefer polarized connectors (JST-XH/keyed Dupont) to avoid reversed connections; solder direct joints once the design is finalized, especially for the mic and amp.
