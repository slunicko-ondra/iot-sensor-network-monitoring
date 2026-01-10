#include "SnowSensor.h"
#include <Arduino.h>
#include <vector>
#include <EEPROM.h>

double SnowSensor::getDistance() const {
    digitalWrite(trigPin, HIGH);
    delayMicroseconds(10);
    digitalWrite(trigPin, LOW);

    const unsigned long duration = pulseIn(echoPin, HIGH);

    const double distance = (duration * 0.0343) / 2;
    return distance;
}

double SnowSensor::median(std::vector<double> numbers) {
    sort(numbers.begin(), numbers.end());
    const size_t size = numbers.size();
    if (size % 2 == 0)
    {
        return numbers[size / 2];
    }
    return (numbers[(size / 2) - 1] + numbers[size / 2]) / 2.0;
}

SnowSensor::SnowSensor(const int trigPin, const int echoPin, const int eepromAddr) {
    this->trigPin = trigPin;
    this->echoPin = echoPin;
    this->eepromAddr = eepromAddr;
    this->snowDepth = 0;
}

double SnowSensor::calibrate(const double snowDepthInput) const {
    const int samples = 10;
    const int delayTime = 500; // ms
    std::vector<double> measurements;

    for (int i = 0; i < samples; i++)
    {
        measurements.push_back(getDistance());
        delay(delayTime);
    }

    const double zeroDepth = median(measurements) - snowDepthInput;
    EEPROM.writeDouble(eepromAddr, zeroDepth);
    EEPROM.commit();
    return zeroDepth;
}

void SnowSensor::measureSnowDepth() {
    const int samples = 5;
    const int delayTime = 500; // ms
    std::vector<double> measurements;

    for (int i = 0; i < samples; i++)
    {
        measurements.push_back(getDistance());
        delay(delayTime);
    }
    const double distance = median(measurements);
    const double depth = EEPROM.readDouble(eepromAddr) - distance;
    snowDepth = (depth > 0) ? (int)round(depth) : 0;
}

int SnowSensor::getSnowDepth() const {
    return snowDepth;
}
