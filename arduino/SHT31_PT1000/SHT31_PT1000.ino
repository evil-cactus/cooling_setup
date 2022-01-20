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

bool enableHeater = false;
uint8_t loopCnt = 0;
const int heaterPin =  2;

const int PT1000_PIN_01 = A0;
const int PT1000_PIN_02 = A2;
const float vt_factor_01 = 1.72;
const float vt_factor_02 = 3.84;
const float offset_01 = -27;
const float offset_02 = -95;

float temp_c_01;
float temp_c_02;

Adafruit_SHT31 sht31 = Adafruit_SHT31();

void setup() {
  Serial.begin(9600);

  while (!Serial)
    delay(10);     // will pause Zero, Leonardo, etc until serial console opens

  Serial.println("SHT31 test");
  if (! sht31.begin(0x44)) {   // Set to 0x45 for alternate i2c addr //connected low (gnd)
  if (! sht31.begin(0x45)) {   // Set to 0x45 for alternate i2c addr //connected high (VDD)
    Serial.println("Couldn't find SHT31");
    while (1) delay(1);
  }}
}


void loop() {
  float t = sht31.readTemperature();
  float h = sht31.readHumidity();

  if (! isnan(t)) {  // check if 'is not a number'
    Serial.println(t); //Serial.print("\t\t");
  } else { 
    Serial.println("Failed to read temperature");
  }
  
  if (! isnan(h)) {  // check if 'is not a number'
    Serial.println(h);
  } else { 
    Serial.println("Failed to read humidity");
  }
  int sensorvalue_01 = analogRead(PT1000_PIN_01);
  float voltage_01 = sensorvalue_01 * (5.0 / 1023.0);
  temp_c_01 = (((voltage_01 * 100) / vt_factor_01) + offset_01);
  Serial.println(voltage_01);
  //Serial.print(" V Temp 01: ");
  Serial.println(temp_c_01, 1);
  int sensorvalue_02 = analogRead(PT1000_PIN_02);
  float voltage_02 = sensorvalue_02 * (5.0 / 1023.0);
  temp_c_02 = (((voltage_02 * 100) / vt_factor_02) + offset_02);
  Serial.println(voltage_02);
  //Serial.print(" V Temp 02: ");
  Serial.println(temp_c_02, 1);
  delay(500);
//  if(t<22.){
//    digitalWrite(heaterPin, HIGH);
//  }
//  else{
//    digitalWrite(heaterPin, LOW);
//  }

  // Toggle heater enabled state every 30 seconds
  // An ~3.0 degC temperature increase can be noted when heater is enabled
//  if (++loopCnt == 30) {
//    enableHeater = !enableHeater;
//    sht31.heater(enableHeater);
//    Serial.print("Heater Enabled State: ");
//    if (sht31.isHeaterEnabled())
//      Serial.println("ENABLED");
//    else
//      Serial.println("DISABLED");
//
//    loopCnt = 0;
//  }
}
