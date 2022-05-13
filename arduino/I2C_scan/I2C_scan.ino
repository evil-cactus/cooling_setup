// --------------------------------------
// i2c_scanner
//
// Modified from https://playground.arduino.cc/Main/I2cScanner/
// --------------------------------------
#include <Arduino.h>
#include <Wire.h>
#include "Adafruit_SHT31.h"

// Set I2C bus to use: Wire, Wire1, etc.
#define WIRE Wire


Adafruit_SHT31 sht31 = Adafruit_SHT31();

void setup() {
  WIRE.begin();	//begin wire communication

  Serial.begin(9600); 	//set baudrate
  while (!Serial)	//waitung for serial monitor
     delay(10);
  Serial.println("\nI2C Scanner is ready");
}


void loop() {
  byte error, address;		//variable for error & i2c address
  int nDevices;

  Serial.println("Scanning...");

  nDevices = 0;
  for(address = 1; address < 127; address++ ) 
  {
    // The i2c_scanner uses the return value of
    // the Write.endTransmisstion to see if
    // a device did acknowledge to the address.
    WIRE.beginTransmission(address);
    error = WIRE.endTransmission();

    if (error == 0)
    {
      Serial.print("I2C device found at address 0x");
      if (address<16) 
        Serial.print("0");
      Serial.print(address,HEX);
      Serial.println("  !");

      // if address found, get temp & humidity 
      sht31.begin(0x70);
      uint16_t stat = sht31.readStatus();
      Serial.print("check add & stat: "); Serial.print(address,HEX); Serial.print(stat, HEX);
      Serial.println();
      
      float t = sht31.readTemperature();
      float h = sht31.readHumidity();

        // temperature
        if (! isnan(t)) {  // check if 'is not a number'
          Serial.print("Temp *C = "); Serial.println(t); //Serial.print("\t\t");
        } 
        else { 
          Serial.println("Failed to read temperature");
        }

        // humidity 
        if (! isnan(h)) {  // check if 'is not a number'
          Serial.print("Hum. % = "); Serial.println(h);
        } 
        else { 
          Serial.println("Failed to read humidity");
         }

       sht31.reset();  

      // next device
      nDevices++;
      }

    // if no address is found, raise error
    else if (error==4) 
    {
      Serial.print("Unknown error at address 0x");
      if (address<16) 
        Serial.print("0");
      Serial.println(address,HEX);
    }    
  }
  if (nDevices == 0)
    Serial.println("No I2C devices found\n"); 
  else
    Serial.println("done\n");

  delay(5000);           // wait 5 seconds for next scan
}
