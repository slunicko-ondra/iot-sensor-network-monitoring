#ifndef SNOWSENSOR_SNOWSENSOR_H
#define SNOWSENSOR_SNOWSENSOR_H

#include <vector>

class SnowSensor {
    int trigPin;
    int echoPin;
    int eepromAddr;
    double getDistance() const;
    static double median(std::vector<double> numbers);
    int snowDepth;

public:
    SnowSensor(int trigPin, int echoPin, int eepromAddr);
    double calibrate(double snowDepthInput = 0) const;
    void measureSnowDepth();
    int getSnowDepth() const;
};


#endif //SNOWSENSOR_SNOWSENSOR_H