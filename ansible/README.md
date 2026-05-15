# Ansible

This directory contains the automation used to deploy the server stack, generate ESPHome sensor assets, and maintain backups.

## Main playbooks

| Playbook                     | Purpose                                                                                    |
|------------------------------|--------------------------------------------------------------------------------------------|
| `server_install.yaml`        | Deploys the server host, Docker stack, and Netbird DNS integration                         |
| `sensor_install.yaml`        | Prepares ESPHome configurations, generates secrets, compiles firmware, and flashes sensors |
| `docker_backup.yaml`         | Creates a backup archive of Docker named volumes and bind mounts                           |
| `docker_backup_restore.yaml` | Restores Docker data and configuration from a backup archive                               |
| `add_ha_bearer.yaml`         | Updates the Prometheus configuration with a Home Assistant bearer token                    |

## Inventory and variables

The repository provides example configuration files that should be copied and customized before use:

- `inventory.example.yaml` → `inventory.yaml`
- `group_vars/all.example.yaml` → `group_vars/all.yaml`
- `group_vars/servers.example.yaml` → `group_vars/servers.yaml`
- `group_vars/sensors.example.yaml` → `group_vars/sensors.yaml`
- `vault.example.yaml` → `vault.yaml`

The default `ansible.cfg` points to `inventory.yaml` and expects a vault password file named `.vault_password`.

**Note:** The `vault.yaml` file should be created with `ansible-vault` and encrypted with a secure password. It contains sensitive values that are used in the configuration templates and should not be committed to version control.

## Roles

### Server roles

- `system_setup` – prepares the target host, enables passwordless sudo, configures the hostname, and adjusts system services for DNS
- `docker` – installs Docker Engine and the Compose plugin
- `iot_stack` – creates the Docker Compose project, renders configuration files, starts services, and configures DNS
- `netbird_dns` – publishes the server as a Netbird DNS nameserver

### Sensor roles

- `prepare_esphome_configs` – renders sensor configuration files from templates
- `prepare_esphome_secrets` – generates and stores ESPHome secrets
- `esphome_firmware` – compiles firmware in a dedicated Python virtual environment
- `upload_esphome_configs` – uploads generated YAML files to the server
- `esphome_flash` – flashes the device over USB or OTA

## Custom Ansible modules

The `library/` directory contains custom modules used by the playbooks:

- `netbird_add_nameserver_group.py` – manages Netbird DNS nameserver groups through the REST API
- `netbird_create_setup_key.py` – creates Netbird setup keys for device enrollment

And two unused modules that were part of the development process:
- `esphome_device_facts.py` – gathers facts from an ESPHome device via the native API
- `esphome_run.py` – runs an ESPHome OTA update from Ansible
