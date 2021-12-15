#define TCAADDR 0x70

#include <Wire.h>
#include <utility/twi.h>  // from Wire library, so we can do bus scanning

#include "Adafruit_SHT31.h"

enum Sensors {NONE,

  // Sensor identifier
  SHT31,

SENSOR_COUNT};

const char *sensorTitles[SENSOR_COUNT] { "None",

  // Sensor Titles
  "Sht31"
};
                       
Sensors slots[8] = {NONE, NONE, NONE, NONE, NONE, NONE, NONE, NONE};

// Temperature - Humidity
Adafruit_SHT31 sht31 = Adafruit_SHT31();


void tcaselect(uint8_t i) {
    if (i > 7) return;
       
    Wire.beginTransmission(TCAADDR);
    Wire.write(1 << i);
    Wire.endTransmission(); 
}

void setup() {
   
    while (!Serial);
    delay(1000);
 
    Wire.begin();

    Serial.begin(115200);

    Serial.println("\nLooking for I2C devices...");
    twi_init();
    for (uint8_t t=0; t<8; t++) {
      tcaselect(t);
      Serial.print("TCA Port #"); Serial.println(t);
 
      for (uint8_t addr = 0; addr<=127; addr++) {
        if (addr == TCAADDR) continue;
     
        uint8_t data;
        if (! twi_writeTo(addr, &data, 0, 1, 1)) {
           if (addr == 0) {}
           else  if (addr == 0x44) {
              if (sht31.begin(0x44)) {
                  slots[t] = SHT31;
                  Serial.println("  --> Found SHT31 Temperature and Humidity Sensor!!");
              }
              else Serial.println("  Can't start SHT31 Temperature and Humidity Sensor!!");
           } else {
            Serial.print("  --> Unrecognized Sensor on address: 0x");
            Serial.println(addr, HEX);
           }
        }
      }
    }
}

void loop() {

  for (uint8_t t=0; t<8; t++) {
    tcaselect(t);
    switch(slots[t]) {
        case SHT31: {
          Serial.println();
          Serial.print(millis()/1000); Serial.print(',');
          Serial.print(t); Serial.print(',');
          Serial.print(sensorTitles[SHT31]); Serial.print(',');
          Serial.print(sht31.readTemperature()); Serial.print(',');
          Serial.println(sht31.readHumidity());
          break;
        }
    }
  }
  delay(1000);
}
