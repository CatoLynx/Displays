// Copyright 2014-2015 Julian Metzler

/*
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

#include <avr/wdt.h>

// Pin configuration for NANO controller board
#define PIN_ROW_A 5
#define PIN_ROW_B 6
#define PIN_ROW_C 10
#define PIN_ROW_D 7
#define PIN_ROW_E 9
#define PIN_ROW_F 8
#define PIN_ROW_G 12
#define PIN_ROW_H 11
#define PIN_OUTPUT_DISABLE 2
#define PIN_DATA 13
#define PIN_SRCLK 3
#define PIN_ORCLK 4
#define PIN_STOP_INDICATOR 14 // Analog In 0

// The baudrate to use for the serial port
#define BAUDRATE 115200

// The number of 8x8 LED matrix modules connected to the controller (= The number of columns divided by 8)
#define NUM_BLOCKS 15

// The maximum number of blocks that a message may consist of
#define MAX_BLOCK_COUNT 100

// The number of milliseconds that should be waited for serial data until a timeout error is returned
#define SERIAL_READ_TIMEOUT 1000

enum displayModes {
  DISP_MODE_STATIC,
  DISP_MODE_SCROLL,
  DISP_MODE_AUTO
};

enum scrollDirections {
  SCROLL_LEFT,
  SCROLL_RIGHT
};

enum scrollModes {
  SCROLL_MODE_REPEAT_ON_END,
  SCROLL_MODE_REPEAT_ON_DISAPPEARANCE,
  SCROLL_MODE_REPEAT_AFTER_GAP
};

enum serialResponses {
  ERR_INV_ACTION_BYTE = 0xE0,
  ERR_INV_BLOCK_COUNT = 0xE1,
  ERR_TIMEOUT = 0xE2,
  ERR_INV_BITMAP_DATA = 0xE3,
  ERR_INV_VALUE = 0xE4
};

enum serialMessageTypes {
  MSG_BITMAP = 0xA0,
  MSG_DISP_MODE = 0xA1,
  MSG_SCROLL_SPEED = 0xA2,
  MSG_SCROLL_DIR = 0xA3,
  MSG_SCROLL_MODE = 0xA4,
  MSG_SCROLL_GAP = 0xA5,
  MSG_PWR_STATE = 0xA6,
  MSG_BLINK_FREQ = 0xA7,
  MSG_SI_STATE = 0xA8,
  MSG_SCROLL_STEP = 0xA9,
  MSG_SI_BLINK_FREQ = 0xAA,
  MSG_PROGRAMMING = 0xAF
};

byte curDispData[MAX_BLOCK_COUNT + NUM_BLOCKS][8]; // + NUM_BLOCKS as a backup space for scrollMode REPEAT_ON_DISAPPEARANCE

int curScrollFrame = 0;
int curBlinkFrame = 0;
int curStopIndBlinkFrame = 0;
int curDispDataBlockCount = NUM_BLOCKS;
int curDispMode = DISP_MODE_AUTO;
int actualDispMode = DISP_MODE_STATIC;
int curScrollDir = SCROLL_LEFT;
int curScrollSpeed = 1;
int curScrollStep = 1;
int curScrollMode = SCROLL_MODE_REPEAT_ON_DISAPPEARANCE;
int curScrollGap = 5;
int scrollWidth = NUM_BLOCKS;
int curScrollPos = NUM_BLOCKS * 8;
int curBlinkFrequency = -1;
int curStopIndBlinkFrequency = -1;
bool curBlinkState = false;
bool curStopIndBlinkState = true;
bool isOn = false;
bool wasOn = false;
bool stopIndicatorOn = false;

void enterProgrammingMode() {
  /*
   * Use the watchdog timer to reset the Arduino as if the reset key had been pressed.
   * The Arduino will only recover from programming mode after the power has been cycled, whether a sketch has been uploaded or not.
   */

  wdt_enable(WDTO_15MS);
  for (;;);
}

void clearDisplayData() {
  memset(curDispData, 0, sizeof curDispData);
}

void writeAllOff() {
  // Row pins have inverse logic due to p-channel FETs
  digitalWrite(PIN_ROW_A, HIGH);
  digitalWrite(PIN_ROW_B, HIGH);
  digitalWrite(PIN_ROW_C, HIGH);
  digitalWrite(PIN_ROW_D, HIGH);
  digitalWrite(PIN_ROW_E, HIGH);
  digitalWrite(PIN_ROW_F, HIGH);
  digitalWrite(PIN_ROW_G, HIGH);
  digitalWrite(PIN_ROW_H, HIGH);
  digitalWrite(PIN_OUTPUT_DISABLE, LOW);
  digitalWrite(PIN_DATA, LOW);
  digitalWrite(PIN_SRCLK, LOW);
  digitalWrite(PIN_ORCLK, LOW);
}

void setStopIndicator(bool state) {
  stopIndicatorOn = state;
  digitalWrite(PIN_STOP_INDICATOR, state);
}

int getPinForRow(int row) {
  if (row < 0) {
    row += 8;
  }
  row %= 8;
  switch (row) {
    case 0:
      return PIN_ROW_A;
    case 1:
      return PIN_ROW_B;
    case 2:
      return PIN_ROW_C;
    case 3:
      return PIN_ROW_D;
    case 4:
      return PIN_ROW_E;
    case 5:
      return PIN_ROW_F;
    case 6:
      return PIN_ROW_G;
    case 7:
      return PIN_ROW_H;
    default:
      return PIN_ROW_A;
  }
}

void modifyValue(int* variable, int value, int min, int max) {
  *variable += value;

  while (*variable < min) {
    *variable += (max - min);
  }

  while (*variable > max) {
    *variable -= (max - min);
  }
}

void updateScrollWidth() {
  scrollWidth = curDispDataBlockCount;

  switch (curScrollMode) {
    case SCROLL_MODE_REPEAT_ON_END:
      scrollWidth = scrollWidth < NUM_BLOCKS ? NUM_BLOCKS : scrollWidth;
      break;

    case SCROLL_MODE_REPEAT_ON_DISAPPEARANCE:
      scrollWidth += NUM_BLOCKS;
      break;

    case SCROLL_MODE_REPEAT_AFTER_GAP:
      scrollWidth += curScrollGap;
      scrollWidth = scrollWidth < NUM_BLOCKS ? NUM_BLOCKS : scrollWidth;
      break;
  }
}

void clearSerialBuffer() {
  while (Serial.available() > 0) {
    Serial.read();
  }
}

void dumpSerialBuffer() {
  while (Serial.available() > 0) {
    Serial.write(Serial.read());
  }
}

void serialResponse(byte value) {
  // Write a response and clear the input buffer
  clearSerialBuffer();
  Serial.write(value);
}

bool readBytesOrTimeout(int* buffer, int length) {
  // Read bytes from the serial port and return a Timeout Error over the serial port if necessary
  // The built-in Serial.readBytes() didn't work because of type issues

  int startTime = millis();

  for (int n = 0; n < length; n++) {
    while (Serial.available() <= 0) {
      int timeTaken = millis() - startTime;
      if (timeTaken >= SERIAL_READ_TIMEOUT || timeTaken < 0) { // Second test in case millis rolled over
        serialResponse(ERR_TIMEOUT);
        return false;
      }
    }

    buffer[n] = Serial.read();
  }

  return true;
}

void doSerialCommunication() {
  /*
  SERIAL PROTOCOL
  Multiple messages can be chained together so that multiple options can be set at once.

  <0xFF> - Start byte
  <1 byte> - Number of individual messages being transmitted

  FOR EACH INDIVIDUAL MESSAGE:
    <1 byte> - Type of message

    If sending a bitmap:
      <1 byte> - Block count of the following bitmap
      <data> - Bitmap data

    Otherwise:
      <1 byte> - Value of the selected option
  */

  // Remember if we hit a timeout
  bool noTimeout = true;

  if (Serial.available() > 0) {
    // Check start byte
    int startByte;
    while (Serial.available() > 0) {
      noTimeout = readBytesOrTimeout(&startByte, 1);
      if (!noTimeout) return;

      if (startByte == 0xFF) {
        break;
      }
    }

    if (startByte != 0xFF) {
      // No error, just discard
      return;
    }

    // OK, we're dealing with an actual message. Disable the matrix to prevent damage and ugly stripes
    // This is gonna be reset when display data is written
    // We're not using the output disable pin because that would require an extra check every multiplex cycle
    // Whereas with this method, the reset occurs "naturally"
    // Also, this assumes that we're only running this routine after the last row has been written
    digitalWrite(PIN_ROW_H, HIGH);

    // Check message count
    int numMsgs;
    noTimeout = readBytesOrTimeout(&numMsgs, 1);
    if (!noTimeout) return;

    // Process individual messages
    for (int n = 0; n < numMsgs; n++) {
      // Check action byte
      int actionByte;
      noTimeout = readBytesOrTimeout(&actionByte, 1);
      if (!noTimeout) return;

      switch (actionByte) {
        case MSG_BITMAP:
          break;

        case MSG_DISP_MODE:
          break;

        case MSG_SCROLL_SPEED:
          break;

        case MSG_SCROLL_DIR:
          break;

        case MSG_SCROLL_MODE:
          break;

        case MSG_SCROLL_GAP:
          break;

        case MSG_PWR_STATE:
          break;

        case MSG_BLINK_FREQ:
          break;

        case MSG_SI_STATE:
          break;

        case MSG_SCROLL_STEP:
          break;

        case MSG_SI_BLINK_FREQ:
          break;
        
        case MSG_PROGRAMMING:
          break;

        default:
          serialResponse(ERR_INV_ACTION_BYTE);
          return;
      }

      int blockCount;
      int columnCount;
      int valueByte;

      switch (actionByte) {
        case MSG_BITMAP:
          // Send bitmap data

          // Check block count
          noTimeout = readBytesOrTimeout(&blockCount, 1);
          if (!noTimeout) return;

          if (blockCount <= 0 || blockCount > MAX_BLOCK_COUNT) {
            serialResponse(ERR_INV_BLOCK_COUNT);
            return;
          }

          // Clear the previous display data and receive the new data
          curDispDataBlockCount = blockCount;
          clearDisplayData();
          for (int block = 0; block < blockCount; block++) {
            for (int idx = 0; idx < 8; idx++) {
              // Read bitmap byte
              int curByte;
              noTimeout = readBytesOrTimeout(&curByte, 1);
              if (!noTimeout) {
                clearDisplayData();
                return;
              }

              if (curByte < 0x00 || curByte > 0xFF) {
                clearDisplayData();
                serialResponse(ERR_INV_BITMAP_DATA);
                return;
              }
              curDispData[block][idx] = (byte) curByte;
            }
          }

          updateScrollWidth();
          if (curDispMode == DISP_MODE_AUTO) {
            if (curDispDataBlockCount > NUM_BLOCKS) {
              actualDispMode = DISP_MODE_SCROLL;
            } else {
              actualDispMode = DISP_MODE_STATIC;
            }
            curScrollPos = NUM_BLOCKS * 8;
          }
          break;

        case MSG_DISP_MODE:
          // Set display mode
          noTimeout = readBytesOrTimeout(&valueByte, 1);
          if (!noTimeout) return;

          switch (valueByte) {
            case 0x00:
              // Static
              curDispMode = DISP_MODE_STATIC;
              actualDispMode = DISP_MODE_STATIC;
              curScrollPos = NUM_BLOCKS * 8;
              break;

            case 0x01:
              // Scrolling
              curDispMode = DISP_MODE_SCROLL;
              actualDispMode = DISP_MODE_SCROLL;
              curScrollPos = NUM_BLOCKS * 8;
              break;

            case 0x02:
              // Automatic
              curDispMode = DISP_MODE_AUTO;
              if (curDispDataBlockCount > NUM_BLOCKS) {
                actualDispMode = DISP_MODE_SCROLL;
              } else {
                actualDispMode = DISP_MODE_STATIC;
              }
              curScrollPos = NUM_BLOCKS * 8;
              break;

            default:
              serialResponse(ERR_INV_VALUE);
              return;
          }
          break;

        case MSG_SCROLL_SPEED:
          // Set scroll speed
          noTimeout = readBytesOrTimeout(&valueByte, 1);
          if (!noTimeout) return;

          // Check value
          if (valueByte < 0x01 || valueByte > 0xFF) {
            serialResponse(ERR_INV_VALUE);
            return;
          }
          curScrollSpeed = valueByte;
          break;

        case MSG_SCROLL_DIR:
          // Set scroll direction
          noTimeout = readBytesOrTimeout(&valueByte, 1);
          if (!noTimeout) return;

          switch (valueByte) {
            case 0x00:
              // Left
              curScrollDir = SCROLL_LEFT;
              break;

            case 0x01:
              // Right
              curScrollDir = SCROLL_RIGHT;
              break;

            default:
              serialResponse(ERR_INV_VALUE);
              return;
          }
          break;

        case MSG_SCROLL_MODE:
          // Set scroll mode
          noTimeout = readBytesOrTimeout(&valueByte, 1);
          if (!noTimeout) return;

          switch (valueByte) {
            case 0x00:
              // Repeat on visibility of end
              curScrollMode = SCROLL_MODE_REPEAT_ON_END;
              break;

            case 0x01:
              // Repeat on disappearance
              curScrollMode = SCROLL_MODE_REPEAT_ON_DISAPPEARANCE;
              break;

            case 0x02:
              // Repeat after a gap of a specified length
              curScrollMode = SCROLL_MODE_REPEAT_AFTER_GAP;
              break;

            default:
              serialResponse(ERR_INV_VALUE);
              return;
          }
          updateScrollWidth();
          break;

        case MSG_SCROLL_GAP:
          // Set scroll gap
          noTimeout = readBytesOrTimeout(&valueByte, 1);
          if (!noTimeout) return;

          // Check value
          if (valueByte < 0x00 || valueByte > NUM_BLOCKS) {
            serialResponse(ERR_INV_VALUE);
            return;
          }
          curScrollGap = valueByte;
          updateScrollWidth();
          break;

        case MSG_PWR_STATE:
          // Enable / disable display
          noTimeout = readBytesOrTimeout(&valueByte, 1);
          if (!noTimeout) return;

          switch (valueByte) {
            case 0x00:
              // Off
              isOn = false;
              break;

            case 0x01:
              // On
              isOn = true;
              break;

            default:
              serialResponse(ERR_INV_VALUE);
              return;
          }
          break;

        case MSG_BLINK_FREQ:
          // Set blink frequency
          noTimeout = readBytesOrTimeout(&valueByte, 1);
          if (!noTimeout) return;

          // Check value
          if (valueByte < 0x00 || valueByte > 0xFF) {
            serialResponse(ERR_INV_VALUE);
            return;
          }

          if (valueByte == 0x00) {
            curBlinkFrequency = -1;
            curBlinkState = false;
            curBlinkFrame = 0;
            digitalWrite(PIN_OUTPUT_DISABLE, LOW);
          } else {
            curBlinkFrequency = valueByte;
          }

          break;

        case MSG_SI_STATE:
          // Enable / disable stop indicator
          noTimeout = readBytesOrTimeout(&valueByte, 1);
          if (!noTimeout) return;

          switch (valueByte) {
            case 0x00:
              // Off
              setStopIndicator(false);
              break;

            case 0x01:
              // On
              setStopIndicator(true);
              break;

            default:
              serialResponse(ERR_INV_VALUE);
              return;
          }
          break;

        case MSG_SCROLL_STEP:
          // Set scroll step
          noTimeout = readBytesOrTimeout(&valueByte, 1);
          if (!noTimeout) return;

          // Check value
          if (valueByte < 0x01 || valueByte > 0xFF) {
            serialResponse(ERR_INV_VALUE);
            return;
          }
          curScrollStep = valueByte;
          break;

        case MSG_SI_BLINK_FREQ:
          // Set stop indicator blink frequency
          noTimeout = readBytesOrTimeout(&valueByte, 1);
          if (!noTimeout) return;

          // Check value
          if (valueByte < 0x00 || valueByte > 0xFF) {
            serialResponse(ERR_INV_VALUE);
            return;
          }

          if (valueByte == 0x00) {
            curStopIndBlinkFrequency = -1;
            curStopIndBlinkState = true;
            curStopIndBlinkFrame = 0;
            digitalWrite(PIN_STOP_INDICATOR, stopIndicatorOn);
          } else {
            curStopIndBlinkFrequency = valueByte;
          }

          break;

        case MSG_PROGRAMMING:
          // Enter programming mode
          serialResponse(0xFF);
          enterProgrammingMode();
          break;
      }
    }

    // Serial communication successful
    serialResponse(0xFF);
  }
}

void writeArrayStatic(byte array[][8]) {
  for (int row = 0; row < 8; row++) {
    for (int block = NUM_BLOCKS - 1; block >= 0; block--) {
      for (byte mask = 1; mask > 0; mask <<= 1) {
        digitalWrite(PIN_DATA, array[block][row] & mask);
        digitalWrite(PIN_SRCLK, HIGH);
        digitalWrite(PIN_SRCLK, LOW);
      }
    }

    digitalWrite(getPinForRow(row - 1), HIGH);
    digitalWrite(PIN_ORCLK, HIGH);
    digitalWrite(PIN_ORCLK, LOW);
    digitalWrite(getPinForRow(row), LOW);

  }
}

void writeArrayScrolling(byte array[][8], int interval = 1, int scrollDirection = SCROLL_LEFT, int scrollStep = 1) {
  // interval is the number of times a frame should be written until it is scrolled

  for (int row = 0; row < 8; row++) {
    for (int block = NUM_BLOCKS - 1; block >= 0; block--) {
      int blockOffset = curScrollPos / 8;
      int maskOffset = curScrollPos % 8;
      int blockOffsetOffset = 0;
      for (int maskPos = 0; maskPos < 8; maskPos++) {
        byte mask = 1;
        int actualMaskPos = maskPos + maskOffset;
        if (actualMaskPos >= 8) {
          actualMaskPos -= 8;
          blockOffsetOffset = 1;
        } else {
          blockOffsetOffset = 0;
        }
        mask <<= actualMaskPos;
        int blockPos = block - blockOffset - blockOffsetOffset;
        digitalWrite(PIN_DATA, array[blockPos < 0 ? blockPos + scrollWidth : blockPos][row] & mask);
        digitalWrite(PIN_SRCLK, HIGH);
        digitalWrite(PIN_SRCLK, LOW);
      }
    }

    digitalWrite(getPinForRow(row - 1), HIGH);
    digitalWrite(PIN_ORCLK, HIGH);
    digitalWrite(PIN_ORCLK, LOW);
    digitalWrite(getPinForRow(row), LOW);
  }

  curScrollFrame++;
  if (curScrollFrame >= interval) {
    curScrollFrame = 0;

    if (scrollDirection == SCROLL_RIGHT) {
      modifyValue(&curScrollPos, scrollStep, 0, scrollWidth * 8);
    } else if (scrollDirection == SCROLL_LEFT) {
      modifyValue(&curScrollPos, -scrollStep, 0, scrollWidth * 8);
    }
  }
}

void setup() {
  clearDisplayData();

  pinMode(PIN_ROW_A, OUTPUT);
  pinMode(PIN_ROW_B, OUTPUT);
  pinMode(PIN_ROW_C, OUTPUT);
  pinMode(PIN_ROW_D, OUTPUT);
  pinMode(PIN_ROW_E, OUTPUT);
  pinMode(PIN_ROW_F, OUTPUT);
  pinMode(PIN_ROW_G, OUTPUT);
  pinMode(PIN_ROW_H, OUTPUT);
  pinMode(PIN_OUTPUT_DISABLE, OUTPUT);
  pinMode(PIN_DATA, OUTPUT);
  pinMode(PIN_SRCLK, OUTPUT);
  pinMode(PIN_ORCLK, OUTPUT);
  pinMode(PIN_STOP_INDICATOR, OUTPUT);

  writeAllOff();
  setStopIndicator(stopIndicatorOn);

  Serial.begin(BAUDRATE);
}

void loop() {
  if (!wasOn && isOn) {
    wasOn = isOn;
  } else if (wasOn && !isOn) {
    writeAllOff();
    wasOn = isOn;
  }

  if (isOn) {
    if (actualDispMode == DISP_MODE_STATIC) {
      writeArrayStatic(curDispData);
    } else if (actualDispMode == DISP_MODE_SCROLL) {
      writeArrayScrolling(curDispData, curScrollSpeed, curScrollDir, curScrollStep);
    }

    if (curBlinkFrequency > 0) {
      curBlinkFrame++;
      if (curBlinkFrame >= curBlinkFrequency) {
        curBlinkFrame = 0;
        curBlinkState = !curBlinkState;
        digitalWrite(PIN_OUTPUT_DISABLE, curBlinkState);
      }
    }
  } else {
    delay(15);
  }

  if (stopIndicatorOn && curStopIndBlinkFrequency > 0) {
    curStopIndBlinkFrame++;
    if (curStopIndBlinkFrame >= curStopIndBlinkFrequency) {
      curStopIndBlinkFrame = 0;
      curStopIndBlinkState = !curStopIndBlinkState;
      digitalWrite(PIN_STOP_INDICATOR, stopIndicatorOn && curStopIndBlinkState);
    }
  }

  doSerialCommunication();
}
