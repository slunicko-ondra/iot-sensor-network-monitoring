# Sensors

This folder contains the sources, templates, examples, and supporting files for the custom sensors used in the project.

ESPHome is the primary framework used for sensor firmware generation and deployment. Ansible renders the per-device YAML files from templates and then compiles or uploads them as needed.

## Directory overview

### `esphome/`

ESPHome-related files, including:

- `ansible_templates/` — Jinja2 templates used by Ansible to generate device-specific YAML files
- `examples/` — ready-to-copy example configurations and supporting data files
- `scripts/` — small helper scripts for common ESPHome tasks

### `misc/`

Supporting assets that are not firmware source code:

- `wiring_diagrams/` — diagrams showing how example sensors are wired
- `3D_models/` — enclosure and casing models for the sensors

### `platformio/`

A historical PlatformIO example for the snow sensor is kept here for reference. The main workflow in this repository is based on ESPHome.

## Documentation

For detailed documentation on how to configure, build, and deploy the sensors, please refer to the [`docs/sensors.md`🔗](../docs/sensors.md) file.

