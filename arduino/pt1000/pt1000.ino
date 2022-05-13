//More Information at: https://www.aeq-web.com/
//Version 1.0 | 03-DEC-2020

const int PT1000_PIN_01 = A0;
const int PT1000_PIN_02 = A2;
const float vt_factor_01 = 1.72;
const float vt_factor_02 = 3.84;
const float offset_01 = -27;
const float offset_02 = -95;

float temp_c_01;
float temp_c_02;

void setup() {
  Serial.begin(9600);
}

void loop() {
  int sensorvalue_01 = analogRead(PT1000_PIN_01);
  float voltage_01 = sensorvalue_01 * (5.0 / 1023.0);
  temp_c_01 = (((voltage_01 * 100) / vt_factor_01) + offset_01);
  Serial.print(voltage_01);
  Serial.print(" V Temp 01: ");
  Serial.println(temp_c_01, 1);
  int sensorvalue_02 = analogRead(PT1000_PIN_02);
  float voltage_02 = sensorvalue_02 * (5.0 / 1023.0);
  temp_c_02 = (((voltage_02 * 100) / vt_factor_02) + offset_02);
  Serial.print(voltage_02);
  Serial.print(" V Temp 02: ");
  Serial.println(temp_c_02, 1);
  delay(500);
}
