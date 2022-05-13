/*************************************************** 
  This is an example for the SHT31-D Humidity & Temp Sensor

  Designed specifically to work with the SHT31-D sensor from Adafruit
  ----> https://www.adafruit.com/products/2857

  These sensors use I2C to communicate, 2 pins are required to  
  interface
 ****************************************************/
 
#include <Arduino.h>
#include <Wire.h>
#include "Adafruit_SHT31.h"

#define TCAADDR 0x70
bool enableHeater = false;
uint8_t loopCnt = 0;
const int heaterPin =  2;

Adafruit_SHT31 sht31 = Adafruit_SHT31();

void tcaselect(uint8_t i){
  if (i > 7) return;

  Wire.beginTransmission(TCAADDR);
  Wire.write(1 << i);
  Wire.endTransmission();
  }

void setup()
{
    while (!Serial);
      delay(1000);
      
    Wire.begin();
    
    Serial.begin(9600);
    Serial.println("\nTCAScanner ready!");
    
    for (uint8_t t=0; t<8; t++) {
      tcaselect(t);
      Serial.print("TCA Port #"); Serial.println(t);

      for (uint8_t addr = 1; addr<=127; addr++) {
        if (addr == TCAADDR) continue;
        Serial.print("test ");Serial.println(addr);
        Wire.beginTransmission(addr);
        if (!Wire.endTransmission()) {
          Serial.print("Found I2C 0x");  Serial.println(addr,HEX);
          //Serial.println("SHT31 test");
          if (! sht31.begin(0x44)) {   // Set to 0x45 for alternate i2c addr //connected low (gnd)
            Serial.println("Couldn't find SHT31");
          }
          if (! sht31.begin(0x45)) {   // Set to 0x45 for alternate i2c addr //connected high (VDD)
            Serial.println("Couldn't find SHT31");
          }
        }
      }
    }
    Serial.println("\ndone");
}

void loop() {
  float t = sht31.readTemperature();
  float h   = sht31.readHumidity();

  if (! isnan(t)) {  // check if 'is not a number'
    Serial.print("Temp *C = "); Serial.println(t); //Serial.print("\t\t");
  } else { 
    Serial.println("Failed to read temperature");
  }
  
  if (! isnan(h)) {  // check if 'is not a number'
    Serial.print("Hum. % = "); Serial.println(h);
  } else { 
    Serial.println("Failed to read humidity");
   }

  delay(1000);
}
