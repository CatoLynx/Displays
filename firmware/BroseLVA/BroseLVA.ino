#include <SoftwareSerial.h>

#define PIN_RX 7
#define PIN_TX 8

#define INPUT_BAUDRATE 57600

SoftwareSerial input(PIN_RX, PIN_TX); // Compile with Rx buffer size 1024

void setup() {
  input.begin(INPUT_BAUDRATE);
  Serial.begin(1200, SERIAL_7E2);
  delay(5000);
  Serial.print("xI00"); // Disable display (stop index 0
  Serial.write(0x0D); // Carriage Return
  Serial.write(0x43); // Checksum
  input.listen();
}

void loop() {
  if (input.available()) {
    Serial.write(input.read());
  }
}

