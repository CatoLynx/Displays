/* (C) 2016 Julian Metzler

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

#include <SoftwareSerial.h>

#define PIN_S0 2
#define PIN_S1 3
#define PIN_S2 4
#define PIN_S3 5
#define PIN_E  6
#define PIN_TX 7
#define PIN_RX 8

#define BAUDRATE             57600
#define PROGRAMMING_BAUDRATE 57600
#define TIMEOUT              5000

SoftwareSerial out(PIN_RX, PIN_TX, true); // Inverted signals because of the ULN2803 / Inverter in the data lines

void selectPort(int address) {
  digitalWrite(PIN_S0, address & 1);
  digitalWrite(PIN_S1, address & 2);
  digitalWrite(PIN_S2, address & 4);
  digitalWrite(PIN_S3, address & 8);
}

void enablePort() {
  digitalWrite(PIN_E, LOW);
}

void disablePort() {
  digitalWrite(PIN_E, HIGH);
}

bool readBytesOrTimeout(byte* buffer, int length) {
  unsigned long startTime = millis();
  for (int n = 0; n < length; n++) {
    while (!Serial.available()) {
      unsigned long timeTaken = millis() - startTime;
      if (timeTaken >= TIMEOUT || timeTaken < 0) { // Second test in case millis rolled over
        return false;
      }
    }
    buffer[n] = Serial.read();
  }
  return true;
}

void doSerialCommunication() {
  /*
   * SERIAL PROTOCOL
   *
   * Because arbitrary data can be transmitted via the serial port, the port selection
   * has to be done with a message prefix:
   *
   *  0xF0> Start Byte
   *    0xCn> Port Selection Byte (0xC0 ... 0xCF)
   *      byte> Message length MSB
   *      byte> Message length LSB
   *      data> Message to Controller
   *
   * Data coming from the controller doesn't need to be prefixed, as we're only accepting
   * port selection data from the hardware serial port.
   */

  // Wait for start byte
  while (!Serial.available());

  // Check start byte
  byte startByte;
  if (!readBytesOrTimeout(&startByte, 1)) return;
  if (startByte != 0xF0) return;

  // Get port selection byte
  byte portByte;
  if (!readBytesOrTimeout(&portByte, 1)) return;
  int address = portByte - 0xC0;

  // Get message length
  byte msgLenMSB, msgLenLSB;
  unsigned int msgLen;
  if (!readBytesOrTimeout(&msgLenMSB, 1)) return;
  if (!readBytesOrTimeout(&msgLenLSB, 1)) return;
  msgLen = (msgLenMSB << 8) + msgLenLSB;

  // Select output port
  selectPort(address);
  enablePort();

  // If message length 0 is specified, listen forever (until the Arduino is reset).
  // This is used to remotely program the display controllers, which requires bidirectional communication with unknown message lengths.
  if (msgLen == 0) {
    Serial.begin(PROGRAMMING_BAUDRATE);
    out.begin(PROGRAMMING_BAUDRATE);
    out.listen();

    while (true) {
      // Transparent Serial proxy
      if (Serial.available()) out.write(Serial.read());
      if (out.available()) Serial.write(out.read());
    }
  }

  // Read and forward the message
  unsigned int numBytes = 0;
  while (numBytes < msgLen) {
    if (!Serial.available()) continue;
    out.write(Serial.read());
    numBytes++;
  }

  // Read and forward the reply until new data comes in or timeout
  unsigned long lastReceive = millis();
  while (!Serial.available() && millis() - lastReceive < TIMEOUT) {
    if (out.available()) {
      Serial.write(out.read());
      lastReceive = millis();
    }
  }

  disablePort();
}

void setup() {
  selectPort(0);
  disablePort();
  pinMode(PIN_S0, OUTPUT);
  pinMode(PIN_S1, OUTPUT);
  pinMode(PIN_S2, OUTPUT);
  pinMode(PIN_S3, OUTPUT);
  pinMode(PIN_E, OUTPUT);
  pinMode(PIN_RX, INPUT_PULLUP); // Force pullup on software UART
  Serial.begin(BAUDRATE);
  out.begin(BAUDRATE);
  out.listen();
}

void loop() {
  doSerialCommunication();
}
