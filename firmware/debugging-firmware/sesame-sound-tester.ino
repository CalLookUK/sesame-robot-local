#include <Arduino.h>
#include "driver/i2s.h"

// ======================================================================
// --- CONFIGURATION ---
// ======================================================================

// I2S pins wired to the MAX98357A amp (S2 Mini build)
#define I2S_BCLK 16
#define I2S_LRC  17
#define I2S_DOUT 18

#define SAMPLE_RATE 16000
#define DEFAULT_TONE_HZ 440
#define DEFAULT_DURATION_MS 2000

const i2s_port_t I2S_PORT = I2S_NUM_0;

// ======================================================================
// --- SETUP ---
// ======================================================================

void setupI2S() {
  i2s_config_t config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX),
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format = I2S_CHANNEL_FMT_RIGHT_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 4,
    .dma_buf_len = 256,
    .use_apll = false,
    .tx_desc_auto_clear = true
  };

  i2s_pin_config_t pins = {
    .bck_io_num = I2S_BCLK,
    .ws_io_num = I2S_LRC,
    .data_out_num = I2S_DOUT,
    .data_in_num = I2S_PIN_NO_CHANGE
  };

  i2s_driver_install(I2S_PORT, &config, 0, NULL);
  i2s_set_pin(I2S_PORT, &pins);
}

void setup() {
  Serial.begin(115200);
  while (!Serial);

  Serial.println("-----------------------------------");
  Serial.println("   Sesame Sound Tester Interface   ");
  Serial.println("-----------------------------------");
  Serial.println("Wiring: BCLK=GPIO16  LRC=GPIO17  DIN=GPIO18");
  Serial.println("Commands:");
  Serial.println("1. tone        -> Play a 440Hz test tone for 2s");
  Serial.println("2. tone,freq   -> Play a test tone at freq Hz for 2s (e.g. 'tone,880')");
  Serial.println("-----------------------------------");

  setupI2S();
  Serial.println("Status: I2S initialized. Ready.");
}

// ======================================================================
// --- MAIN LOOP ---
// ======================================================================

void loop() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();

    if (input.length() == 0) return;

    int commaIndex = input.indexOf(',');
    String cmd = (commaIndex != -1) ? input.substring(0, commaIndex) : input;

    if (!cmd.equalsIgnoreCase("tone")) {
      Serial.println("Error: Unknown command. Use 'tone' or 'tone,freq'.");
      return;
    }

    int freq = DEFAULT_TONE_HZ;
    if (commaIndex != -1) {
      freq = input.substring(commaIndex + 1).toInt();
      if (freq < 20 || freq > 8000) {
        Serial.println("Error: freq must be between 20-8000 Hz");
        return;
      }
    }

    playTone(freq, DEFAULT_DURATION_MS);
  }
}

// ======================================================================
// --- HELPER FUNCTIONS ---
// ======================================================================

void playTone(int freq, int durationMs) {
  Serial.print("Playing "); Serial.print(freq); Serial.println("Hz tone...");

  const int samplesPerCycle = SAMPLE_RATE / freq;
  int16_t buffer[2]; // L, R (identical - MAX98357A only needs one channel)
  size_t bytesWritten;
  unsigned long start = millis();

  while (millis() - start < (unsigned long)durationMs) {
    for (int i = 0; i < samplesPerCycle; i++) {
      int16_t sample = (int16_t)(sinf(2.0f * PI * i / samplesPerCycle) * 8000);
      buffer[0] = sample;
      buffer[1] = sample;
      i2s_write(I2S_PORT, buffer, sizeof(buffer), &bytesWritten, portMAX_DELAY);
    }
  }

  Serial.println("Done.");
}
