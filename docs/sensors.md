# Sensors Documentation

This section describes how the custom sensors are prepared, built, and flashed.

ESPHome is the primary framework used for the sensor firmware. Ansible renders per-device configuration files, generates secrets, compiles the firmware, and can flash the devices over USB or OTA.

## Sensor workflow

The sensor deployment playbook is `ansible/sensor_install.yaml` and it performs five stages:

1. Prepare ESPHome configuration files on the sensor inventory host.
2. Generate the shared and per-device secrets.
3. Compile the firmware.
4. Flash the devices over USB or OTA.
5. Upload the generated configuration files to the server.

## Supported sensor templates

The ESPHome templates live in `sensors/esphome/ansible_templates/` and currently include:

- `blank_sensor.yaml.j2`
- `one_wire_multi_temp.yaml.j2`
- `snow_sensor.yaml.j2`
- `solar_sensor.yaml.j2`
- `solar_sensor_zigbee.yaml.j2`
- `temperature_single.yaml.j2`
- `zigbee_rain.yaml.j2`

Matching example files are available in `sensors/esphome/examples/`.

## Inventory and variables

Sensor hosts are defined in `ansible/inventory.yaml` using the `sensors` group. Variables common for all sensors can be defined in `ansible/group_vars/sensors.yaml` (see [`group_vars/sensors.example.yaml`🔗](../ansible/group_vars/sensors.example.yaml) for reference). Per-device variables can be defined in the host definition in the inventory file.

The most important values are:

- `config_name` — selects the ESPHome template without the `.yaml` suffix
- `esp_platform` — `esp32` or `esp8266`
- `esp_variant` — the ESP32 variant when applicable
- `esp_board` — the ESP8266 board definition when applicable
- `default_gateway`, `default_subnet`, and `mqtt_broker` — used by the generated sensor configuration

Shared Wi-Fi and MQTT credentials are stored in `ansible/vault.yaml` and copied into the generated ESPHome secrets file.

## Flashing methods

Selected flashing method is determined by the `flash_method` variable. It can be set to `usb` (default) or `ota`. For example:

```bash
ansible-playbook sensor_install.yaml --limit snow_sensor_1 -e "flash_method=ota"
```

### USB flashing

USB flashing is interactive. The playbook prompts the user to:

- plug in the sensor board
- wait for the serial device to appear
- confirm or override the detected serial port

This mode is useful for brand-new devices or for boards that are not yet reachable over the network.

### OTA flashing

OTA flashing is used when the device is already reachable on the network. In this mode Ansible checks whether `ansible_host` contains a valid IP address and then runs the ESPHome upload command against that address.

This method requires a device with ESPHome firmware with enabled OTA support. It does not work with Zigbee-only devices.

## Helper scripts

The `sensors/esphome/scripts/` directory contains small utilities for working with ESPHome devices, such as:

- `generate_key.sh` – generates a random 32-character ESPHome API key
- `erase_flash.sh` – erases the flash memory of an ESP device over USB using `esptool.py` (useful for resetting Zigbee devices to factory defaults)

## Example and reference files

The `sensors/esphome/examples/` directory contains ready-to-copy example configurations, including:

- sensor YAML examples
- `secrets.example.yaml`
- `partitions_zb.csv` for ESP32-C6 Zigbee devices

## Sensor hardware

All hardware-specific notes, such as wiring diagrams, pinouts, and 3D models of enclosures, are stored in the [`sensors/misc/`🔗](../sensors/misc) directory.

## PlatformIO note

ESPHome is the main approach used in this repository. A historical PlatformIO example for the snow sensor is still available in `sensors/platformio/snowSensor/` for reference.
