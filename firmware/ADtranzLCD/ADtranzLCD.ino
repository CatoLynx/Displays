/*
(C) 2016 Julian Metzler

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

// COMPILE WITH RX BUFFER SIZE 512

#include <avr/wdt.h>
#include <SPI.h>
#include <TimerOne.h>
#include <GV60LCD.h>

/*
 * PIN DECLARATIONS
 */

#define PIN_LATCH     9
#define PIN_BIAS      8
#define PIN_LIGHT     5
#define PIN_LIGHT_DIM 4

/*
 * GLOBAL CONSTANTS
 */

#define BAUDRATE       57600
#define SERIAL_TIMEOUT 5000
#define NUM_PANELS     3
#define PANEL_WIDTH    48

// Screen is n x 26 pixels, stored in a (n/8) byte (= n bits) x 26 byte array
byte framebuf[NUM_PANELS * PANEL_WIDTH / 8][26] = {0};
GV60LCD screen(PIN_LATCH, PIN_BIAS, NUM_PANELS, PANEL_WIDTH);

enum SERIAL_STATUSES {
  SUCCESS = 0xFF,
  TIMEOUT = 0xE0,
  ERROR = 0xEE,
};

/*
 * PROGRAM CODE
 */

void enterProgrammingMode() {
  /*
   * Use the watchdog timer to reset the Arduino as if the reset key had been pressed.
   * The Arduino will only recover from programming mode after the power has been cycled, whether a sketch has been uploaded or not.
   */

  wdt_enable(WDTO_15MS);
  for (;;);
}

void setBacklight(int level) {
  /*
   * Set the LCD backlight either on, off, or dim
   */

  switch (level) {
    case 0: {
        digitalWrite(PIN_LIGHT, LOW);
        digitalWrite(PIN_LIGHT_DIM, LOW);
        break;
      }

    case 1: {
        digitalWrite(PIN_LIGHT_DIM, HIGH);
        digitalWrite(PIN_LIGHT, HIGH);
        break;
      }

    case 2:
    default: {
        digitalWrite(PIN_LIGHT_DIM, LOW);
        digitalWrite(PIN_LIGHT, HIGH);
        break;
      }
  }
}

void setMatrix(byte* bitmap) {
  /*
   * Write a bitmap to the matrix.
   */

  screen.output(bitmap);
}

void clearSerialBuffer() {
  while (Serial.available() > 0) {
    Serial.read();
  }
}

void serialResponse(byte status) {
  Serial.write(status);
}

bool readBytesOrTimeout(byte* buffer, int length) {
  int startTime = millis();
  for (int n = 0; n < length; n++) {
    while (!Serial.available()) {
      int timeTaken = millis() - startTime;
      if (timeTaken >= SERIAL_TIMEOUT || timeTaken < 0) { // Second test in case millis rolled over
        return false;
      }
    }
    buffer[n] = Serial.read();
  }
  return true;
}

bool readBytesOrTimeoutError(byte* buffer, int length) {
  bool success = readBytesOrTimeout(buffer, length);
  if (!success) {
    serialResponse(TIMEOUT);
  }
  return success;
}

void receiveBitmap() {
  // Receive number of columns
  byte numBytesMSB, numBytesLSB;
  if (!readBytesOrTimeoutError(&numBytesMSB, 1)) return;
  if (!readBytesOrTimeoutError(&numBytesLSB, 1)) return;
  int numBytes = (numBytesMSB << 8) + numBytesLSB;

  // Receive bitmap data
  byte bitmap[numBytes];
  if (!readBytesOrTimeoutError(bitmap, numBytes)) return;

  // Write the bitmap to the matrix
  setMatrix(bitmap);
  memcpy(framebuf, bitmap, numBytes);
}

void doSerialCommunication() {
  /*
   * SERIAL PROTOCOL
   *
   * Explanation:
   *   0x00> - Byte from PC to Arduino
   *  <0x00  - Byte from Arduino to PC
   *
   * Status codes:
   *   <0xFF  - Success
   *   <0xE0  - Timeout while receiving serial data
   *   <0xEE  - Generic Error
   *
   * 0xFF> - Start Byte
   * 0xAn> - Action byte:
   *   0xA0> - Send bitmap:
   *     byte> - Number of bytes to be sent (MSB)
   *     byte> - Number of bytes to be sent (LSB)
   *     data> - Bitmap data
   *  <byte  - Status code
   *   0xA1> - Set LCD backlight
   *     byte> - Backlight level (0, 1, 2)
   *
   *   0xAF> - Enter programming mode
   *  <byte - Confirmation (always 0xFF)
   */

  if (!Serial.available()) return;
  // Check for start byte
  byte startByte;
  if (!readBytesOrTimeout(&startByte, 1)) return;
  if (startByte != 0xFF) return;

  // Check action byte
  byte actionByte;
  if (!readBytesOrTimeoutError(&actionByte, 1)) return;
  switch (actionByte) {
    // Send bitmap
    case 0xA0: {
        receiveBitmap();
        clearSerialBuffer();
        serialResponse(SUCCESS);
        break;
      }

    // Set LCD backlight
    case 0xA1: {
        byte valueByte;
        if (!readBytesOrTimeoutError(&valueByte, 1)) return;
        setBacklight(valueByte);
        clearSerialBuffer();
        serialResponse(SUCCESS);
        break;
      }

    // Enter programming mode
    case 0xAF: {
        clearSerialBuffer();
        serialResponse(SUCCESS);
        enterProgrammingMode();
        break;
      }
  }
}

void setup() {
  Serial.begin(BAUDRATE);

  screen.init();
  screen.output(*framebuf);

  pinMode(PIN_LIGHT, OUTPUT);
  pinMode(PIN_LIGHT_DIM, OUTPUT);

  setBacklight(1);
  delay(2000);
  setBacklight(2);
  delay(2000);
  setBacklight(0);
}

void loop() {
  doSerialCommunication();
}
