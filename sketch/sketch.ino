// gait-identifier: MPU-6050 on the ankle (header SDA/SCL, address 0x68).
//
// Python calls imu_check() and imu_read() for raw samples
// "ax,ay,az,gx,gy,gz" in g and deg/s (ranges: ±16 g, ±2000 deg/s, wide enough for running).

#include <Wire.h>
#include "Arduino_RouterBridge.h"

const uint8_t ADDR = 0x68;
const uint8_t REG_GYRO_CONFIG = 0x1B;
const uint8_t REG_ACCEL_CONFIG = 0x1C;
const uint8_t REG_ACCEL_XOUT_H = 0x3B;
const uint8_t REG_PWR_MGMT_1 = 0x6B;
const uint8_t REG_WHO_AM_I = 0x75;

const uint8_t RANGE_MAX = 0x18;     // ±16 g / ±2000 deg/s in the config registers
const float ACCEL_LSB = 2048.0;     // counts per g at ±16 g
const float GYRO_LSB = 16.4;        // counts per deg/s at ±2000 deg/s

bool found = false;

void write_reg(uint8_t reg, uint8_t val) {
    Wire.beginTransmission(ADDR);
    Wire.write(reg);
    Wire.write(val);
    Wire.endTransmission();
}

// Point at reg, then request n bytes
void request(uint8_t reg, uint8_t n) {
    Wire.beginTransmission(ADDR);
    Wire.write(reg);
    Wire.endTransmission(false);
    Wire.requestFrom(ADDR, n);
}

// Raw counts: ax, ay, az, temp, gx, gy, gz
void read_raw(int16_t v[7]) {
    request(REG_ACCEL_XOUT_H, 14);
    for (int i = 0; i < 7; i++) {
        uint8_t hi = Wire.read();
        uint8_t lo = Wire.read();
        v[i] = (int16_t)((hi << 8) | lo);
    }
}

String imu_check() {
    if (!found) return "not found at 0x68";
    request(REG_WHO_AM_I, 1);
    return "found, whoami=0x" + String(Wire.read(), HEX);
}

String imu_read() {
    if (!found) return "";
    int16_t v[7];
    read_raw(v);
    String s;
    for (int i = 0; i < 3; i++) s += String(v[i] / ACCEL_LSB, 3) + ",";
    for (int i = 4; i < 7; i++) s += String(v[i] / GYRO_LSB, 1) + (i < 6 ? "," : "");
    return s;
}

void setup() {
    Wire.begin();
    Wire.beginTransmission(ADDR);
    found = Wire.endTransmission() == 0;
    if (found) {
        write_reg(REG_PWR_MGMT_1, 0);  // wake from sleep
        write_reg(REG_GYRO_CONFIG, RANGE_MAX);
        write_reg(REG_ACCEL_CONFIG, RANGE_MAX);
    }

    Bridge.begin();
    Bridge.provide_safe("imu_check", imu_check);
    Bridge.provide_safe("imu_read", imu_read);
}

void loop() {
}
