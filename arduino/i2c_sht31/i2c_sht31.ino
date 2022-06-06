#include <Arduino.h>
#include <Wire.h>
extern "C" {
#include "utility/twi.h" // from Wire library, so we can do bus scanning
}
#include "Adafruit_SHT31.h"

// Set I2C bus to use: Wire, Wire1, etc.
#define WIRE Wire
// define multiplexer with default address
#define TCAADDR 0x70

Adafruit_SHT31 sht31 = Adafruit_SHT31();

enum Sensors { NONE,
               // Sensor identifier
               SHT31,
               SENSOR_COUNT
};

const char* sensorTitles[SENSOR_COUNT]{"None",
                                       // Sensor Titles
                                       "Sht31"};

Sensors slots[8] = {NONE, NONE, NONE, NONE, NONE, NONE, NONE, NONE};

// function to scan all 8 channels
void tcaselect(uint8_t i) {
  if (i > 7) return;

  Wire.beginTransmission(TCAADDR);
  Wire.write(1 << i);
  Wire.endTransmission();
}

// adress info
uint16_t addr_info;
// const int rows;
// const int columns = 3;
int info_array[] = {0, 0, 0, 0, 0, 0, 0, 0};

// standard setup
void setup() {
  WIRE.begin(); // begin wire communication

  Serial.begin(9600); // set baudrate
  while (!Serial)     // waitung for serial monitor
    delay(10);
  Serial.println("\nTCAScanner ready!");

  for (uint8_t t = 0; t < 8; t++) { // scan other all eight channels
    tcaselect(t);
    Serial.print("TCA Port #");
    Serial.println(t); // print found port

    for (uint8_t addr = 0; addr <= 127; addr++) { // print found address from the corresponding channel
      if (addr == TCAADDR) continue;
      Wire.beginTransmission(addr);
      //          Serial.println("test1");
      if (!Wire.endTransmission()) {
        Serial.print("Found I2C 0x");
        Serial.println(addr, HEX);
        if (sht31.begin(0x44)) {
          slots[t]      = SHT31;
          addr_info     = addr;
          info_array[t] = t;
          Serial.print("TCA Port #");
          Serial.print(t);
          Serial.print(" Found I2C 0x");
          Serial.print(addr, HEX);
          Serial.println("  --> Found SHT31 Temperature and Humidity Sensor!!");
        }
        //             if (sht31.begin(0x45)) {
        //                      slots[t] = SHT31;
        //                      addr_info = addr;
        //                      info_array[t] = t ;
        //                      Serial.print("TCA Port #");
        //                      Serial.print(t);
        //                      Serial.print(" Found I2C 0x");
        //                      Serial.print(addr,HEX);
        //                      Serial.println("  --> Found SHT31 Temperature and Humidity Sensor!!");
        //                  }
        else
          Serial.println("  Can't start SHT31 Temperature and Humidity Sensor!!");
      }
    }
  }
}

void loop() {
  for (uint8_t t = 0; t < 8; t++) {
    tcaselect(t);
    switch (slots[t]) {
    case SHT31: {
      // Serial.println();
      // for( int i = 0; i < sizeof(info_array); i++){
      // Serial.print(info_array[i]);
      //}
      // Serial.println();
      // Serial.print(millis()/1000); Serial.print(',');
      // Serial.print("Found I2C 0x");
      // Serial.print(addr_info, HEX);
      // Serial.print(" at ");
      // Serial.print(" TCA Port #");
      // Serial.print(t);
      // Serial.print(" .This is slot: "); Serial.print(t); Serial.print(',');
      // Serial.print("Sensor Title: "); Serial.print(sensorTitles[SHT31]); Serial.print(',');
      // Serial.print("Temperature/°C: "); Serial.print(sht31.readTemperature()); Serial.print(',');
      // Serial.print("Humidity: "); Serial.println(sht31.readHumidity());

      float temp = sht31.readTemperature();
      float hum  = sht31.readHumidity();
      Serial.print("1 ");
      Serial.print(t);
      Serial.print(",");
      Serial.print(temp);
      Serial.print("T,");
      Serial.print(hum);
      Serial.print("H");
      Serial.println();

      break;
    }
    }
  }
  delay(1000);
}
