#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_BMP280.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <EEPROM.h>

#define ELEGANTOTA_USE_ASYNC_WEBSERVER 1
#include <ElegantOTA.h>
#include <ESPAsyncWebServer.h>
#include <AsyncTCP.h>

#include <SnowSensor.h>
#include <HtmlPages.h>

#define TRIG_PIN 32
#define ECHO_PIN 33
#define EEPROM_SIZE 128

struct EepromData {
    uint32_t memory_check;
    double sensor_zero_depth;
    char wifi_ssid[32];
    char wifi_password[32];
    char wifi_ip[16];
    char wifi_gateway[16];
    char mqtt_broker_ip[16];
} eeprom_data;

const uint32_t MEMORY_CHECK_VALUE = 0x600DCAFE;

SnowSensor snowSensor(TRIG_PIN, ECHO_PIN, offsetof(EepromData, sensor_zero_depth));
Adafruit_BMP280 bmp; // I2C

void saveConfig() {
    eeprom_data.memory_check = MEMORY_CHECK_VALUE;
    EEPROM.put(0, eeprom_data);
    EEPROM.commit();
}

void loadConfig() {
    EEPROM.get(0, eeprom_data);
    if (eeprom_data.memory_check != MEMORY_CHECK_VALUE) {
        strcpy(eeprom_data.wifi_ssid, "DefaultSSID");
        strcpy(eeprom_data.wifi_password, "DefaultPass");
        strcpy(eeprom_data.wifi_ip, "10.0.10.20");
        strcpy(eeprom_data.wifi_gateway, "10.0.10.1");
        strcpy(eeprom_data.mqtt_broker_ip, "10.0.10.10");
        eeprom_data.sensor_zero_depth = 0.0;
    }
}

// MQTT Broker
auto publish_topic = "weather";
auto subscribe_topic = "calibrateSnow";
auto calibration_status_topic = "calibrationStatus";
auto mqtt_username = "esp32snow";
auto mqtt_password = "public";
constexpr int mqtt_port = 1883;

// web server
AsyncWebServer server(80);
unsigned long ota_progress_millis = 0;

WiFiClient espClient;
PubSubClient client(espClient);

void callback(char* topic, byte* payload, unsigned int length) {
    Serial.print("Message arrived in topic: ");
    Serial.println(topic);

    // payload to string
    String message;
    for (int i = 0; i < length; i++) {
        message += (char)payload[i];
    }

    Serial.print("Message: ");
    Serial.println(message);
    Serial.println("-----------------------");

    // calibration
    if (String(topic) == subscribe_topic) {
        const double value = message.toDouble();
        const double result = snowSensor.calibrate(value);
        Serial.print("Calibration value received: ");
        Serial.println(value);
        const String resultString = "Calibration OK: " + String(result);
        client.publish(calibration_status_topic, resultString.c_str());
    }
}

void onOTAStart() {
    // Log when OTA has started
    Serial.println("OTA update started!");
    // <Add your own code here>
}

void onOTAProgress(size_t current, size_t final) {
    // Log every 1 second
    if (millis() - ota_progress_millis > 1000) {
        ota_progress_millis = millis();
        Serial.printf("OTA Progress Current: %u bytes, Final: %u bytes\n", current, final);
    }
}

void onOTAEnd(bool success) {
    // Log when OTA has finished
    if (success) {
        Serial.println("OTA update finished successfully!");
    } else {
        Serial.println("There was an error during OTA update!");
    }
    // <Add your own code here>
}

String getValuesJson() {
    int snowDepth = snowSensor.getSnowDepth();
    float temperature = bmp.readTemperature();
    float pressure = bmp.readPressure() / 100.0;
    String result = "{\"snow_depth_cm\": " + String(snowDepth) +
        ", \"temperature_c\": " + String(temperature) +
        ", \"pressure_hpa\": " + String(pressure) + "}";
    return result;
}

void setup() {
    pinMode(TRIG_PIN, OUTPUT);
    pinMode(ECHO_PIN, INPUT);
    EEPROM.begin(EEPROM_SIZE);

    Serial.begin(9600);

    while (!Serial) delay(100); // wait for native usb
    Serial.println(F("BMP280 test"));
    unsigned status;
    status = bmp.begin(0x76);
    if (!status)
    {
        Serial.println(F("Could not find a valid BMP280 sensor, check wiring or "
            "try a different address!"));
        Serial.print("SensorID was: 0x");
        Serial.println(bmp.sensorID(), 16);
        Serial.print("        ID of 0xFF probably means a bad address, a BMP 180 or BMP 085\n");
        Serial.print("   ID of 0x56-0x58 represents a BMP 280,\n");
        Serial.print("        ID of 0x60 represents a BME 280.\n");
        Serial.print("        ID of 0x61 represents a BME 680.\n");
        while (1) delay(10);
    }

    /* Default settings from datasheet. */
    bmp.setSampling(Adafruit_BMP280::MODE_NORMAL, /* Operating Mode. */
                    Adafruit_BMP280::SAMPLING_X2, /* Temp. oversampling */
                    Adafruit_BMP280::SAMPLING_X16, /* Pressure oversampling */
                    Adafruit_BMP280::FILTER_X16, /* Filtering. */
                    Adafruit_BMP280::STANDBY_MS_500); /* Standby time. */

    // Connecting to a Wi-Fi network
    loadConfig();
    WiFi.begin(eeprom_data.wifi_ssid, eeprom_data.wifi_password);
    Serial.print("Connecting to WiFi");
    unsigned long startAttemptTime = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - startAttemptTime < 20000) {
        delay(500);
        Serial.print(".");
    }

    if (WiFi.status() == WL_CONNECTED) {
        // Set static IP
        IPAddress local_IP, gateway;
        local_IP.fromString(eeprom_data.wifi_ip);
        gateway.fromString(eeprom_data.wifi_gateway);
        WiFi.config(local_IP, gateway, IPAddress(255,255,255,0));
        Serial.println("\nConnected! IP Address: " + WiFi.localIP().toString());
    } else {
        // Switch to Access Point mode
        Serial.println("\nFailed to connect. Switching to AP mode...");
        WiFi.softAP("Snow_sensor");
    }

    //connecting to a mqtt broker
    client.setServer(eeprom_data.mqtt_broker_ip, mqtt_port);
    client.setCallback(callback);
    int attempts = 0;
    while (!client.connected() && attempts < 5)
    {
        String client_id = "esp32-client-";
        client_id += String(WiFi.macAddress());
        Serial.printf("The client %s connects to the public MQTT broker\n", client_id.c_str());
        if (client.connect(client_id.c_str(), mqtt_username, mqtt_password))
        {
            Serial.println("Public EMQX MQTT broker connected");
        }
        else
        {
            Serial.print("failed with state ");
            Serial.print(client.state());
            delay(2000);
        }
        attempts++;
    }
    if (client.connected())
    {
        client.subscribe(subscribe_topic);
    }

    //  start web server and ElegantOTA
    server.on("/", HTTP_GET, [](AsyncWebServerRequest *req){
        req->send(200, "text/html", index_html);
    });

    server.on("/", HTTP_POST, [](AsyncWebServerRequest *req) {
        if (req->hasParam("snow_depth", true)) {
            String snowDepthStr = req->getParam("snow_depth", true)->value();
            double snowDepth = snowDepthStr.toDouble();
            double result = snowSensor.calibrate(snowDepth);
            req->send(200, "text/html", "Calibration done! Sensor zero depth: " + String(result) + " cm<br><a href='/'>Go Back</a>");
        } else {
            req->send(400, "text/html", "Missing snow_depth parameter!<br><a href='/'>Go Back</a>");
        }
    });

    server.on("/sensor", HTTP_GET, [](AsyncWebServerRequest *req){
        req->send(200, "application/json", getValuesJson());
    });

    server.on("/wifi", HTTP_GET, [](AsyncWebServerRequest *request) {
        String page = wifi_html;
        page.replace("%SSID%", eeprom_data.wifi_ssid);
        page.replace("%IP%", eeprom_data.wifi_ip);
        page.replace("%GATEWAY%", eeprom_data.wifi_gateway);
        request->send(200, "text/html", page);
    });

    server.on("/wifi", HTTP_POST, [](AsyncWebServerRequest *request) {
        if (request->hasParam("ssid", true) && request->hasParam("password", true) &&
            request->hasParam("ip", true) && request->hasParam("gateway", true)) {

            strcpy(eeprom_data.wifi_ssid, request->getParam("ssid", true)->value().c_str());
            strcpy(eeprom_data.wifi_password, request->getParam("password", true)->value().c_str());
            strcpy(eeprom_data.wifi_ip, request->getParam("ip", true)->value().c_str());
            strcpy(eeprom_data.wifi_gateway, request->getParam("gateway", true)->value().c_str());
            saveConfig();
            request->send(200, "text/html", "Settings Saved! Restarting...");
            delay(2000);
            ESP.restart();
        } else {
            request->send(400, "text/html", "Missing Parameters!");
        }
    });

    server.on("/mqtt", HTTP_GET, [](AsyncWebServerRequest *request) {
        String page = mqtt_html;
        page.replace("%BROKER%", eeprom_data.mqtt_broker_ip);
        request->send(200, "text/html", page);
    });

    server.on("/mqtt", HTTP_POST, [](AsyncWebServerRequest *request) {
        if (request->hasParam("broker", true)) {
            strcpy(eeprom_data.mqtt_broker_ip, request->getParam("broker", true)->value().c_str());
            saveConfig();
            request->send(200, "text/html", "Settings Saved! Restarting...");
            delay(2000);
            ESP.restart();
        } else {
            request->send(400, "text/html", "Missing Parameters!");
        }
    });

    ElegantOTA.begin(&server);    // Start ElegantOTA
    // ElegantOTA callbacks
    ElegantOTA.onStart(onOTAStart);
    ElegantOTA.onProgress(onOTAProgress);
    ElegantOTA.onEnd(onOTAEnd);

    server.begin();
    Serial.println("HTTP server started");

}

void loop() {
    client.loop();
    ElegantOTA.loop();

    // publish data every 2 seconds
    static unsigned long lastPublish = 0;
    static unsigned long lastMeasure = 0;
    if (millis() - lastPublish > 2000)
    {
        lastPublish = millis();
        Serial.print("Publishing payload: ");
        String payload = getValuesJson();
        Serial.println(payload);
        client.publish(publish_topic, payload.c_str());
    }
    if (millis() - lastMeasure > 9000)
    {
        lastMeasure = millis();
        Serial.println("Measuring snow depth...");
        snowSensor.measureSnowDepth();
        Serial.println(snowSensor.getSnowDepth());
    }
}
