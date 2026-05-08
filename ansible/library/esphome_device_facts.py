#!/usr/bin/python

# Copyright: (c) 2026, Ondřej Ježek
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from aioesphomeapi import DeviceInfo

DOCUMENTATION = r'''
---
module: esphome_device_facts

short_description: Gathers facts from an ESPHome device via the native API.

version_added: "1.0.0"

description:
  - Connects to an ESPHome device over its native API and returns basic device facts.
  - Retrieves device metadata and the list of exposed entities.
  - This is a read-only module and never changes the device state.

options:
    host:
        description:
            - Hostname or IP address of the ESPHome device.
            - Use the device address reachable from the Ansible controller.
        required: true
        type: str
    port:
        description:
            - ESPHome native API port.
            - Defaults to C(6053), which is the standard ESPHome API port.
        required: false
        type: int
        default: 6053

    noise_psk:
        description:
            - Optional Noise PSK for encrypted API connections.
            - Use this when the device is configured with ESPHome API encryption.
        required: false
        type: str
        no_log: true

    password:
        description:
            - Optional plaintext API password for devices that still use password authentication.
            - Leave unset when the device uses API encryption instead.
        required: false
        type: str
        no_log: true

author:
    - Ondřej Ježek

notes:
    - The module only reads data from the device and always returns C(changed=false).
    - The returned facts include the device metadata and the list of entities exposed by ESPHome.
    - Services are queried from the device API as part of discovery, but are not currently returned.

requirements:
    - aioesphomeapi
'''

EXAMPLES = r'''
# Gather facts from an ESPHome device using the default native API port
- name: Gather facts from snow sensor
  esphome_device_facts:
    host: 10.0.10.30
  register: snow_sensor_facts

# Gather facts from an encrypted ESPHome device
- name: Gather facts from encrypted device
  esphome_device_facts:
    host: snow-sensor.local
    port: 6053
    noise_psk: "{{ esphome_noise_psk }}"
  register: encrypted_sensor_facts

# Gather facts from a device that still uses API password authentication
- name: Gather facts from password-protected device
  esphome_device_facts:
    host: 10.0.10.31
    password: "{{ esphome_api_password }}"
  register: password_sensor_facts
'''

RETURN = r'''
changed:
    description:
        - Always C(false), because the module only collects facts.
    type: bool
    returned: always
    sample: false

esphome_facts:
    description:
        - Structured facts returned from the ESPHome device.
        - Contains the API version, device metadata, and the list of entities.
    type: dict
    returned: always
    sample:
        api_version: "2025.2"
        device_info:
            name: "Snow Sensor"
            mac_address: "AA:BB:CC:DD:EE:FF"
            esphome_version: "2025.4.0"
            compilation_time: "Apr 28 2026, 12:30:00"
            model: "ESP32-D0WDQ6"
            has_deep_sleep: false
        entities:
            - object_id: "snow_distance"
              key: 1
              name: "Snow Distance"
              type: "SensorInfo"
            - object_id: "snow_height"
              key: 2
              name: "Snow Height"
              type: "SensorInfo"

api_version:
    description:
        - ESPHome API version reported by the device.
    type: str
    returned: when supported by the device
    sample: "2025.2"

device_info:
    description:
        - Basic metadata about the ESPHome device.
    type: dict
    returned: when supported by the device
    contains:
        name:
            description: Device name reported by ESPHome.
            type: str
            returned: always
            sample: "Snow Sensor"
        mac_address:
            description: MAC address of the device.
            type: str
            returned: always
            sample: "AA:BB:CC:DD:EE:FF"
        esphome_version:
            description: ESPHome firmware version running on the device.
            type: str
            returned: always
            sample: "2025.4.0"
        compilation_time:
            description: Firmware compilation timestamp.
            type: str
            returned: always
            sample: "Apr 28 2026, 12:30:00"
        model:
            description: Device model reported by ESPHome.
            type: str
            returned: always
            sample: "ESP32-D0WDQ6"
        has_deep_sleep:
            description: Whether the device supports deep sleep.
            type: bool
            returned: always
            sample: false

entities:
    description:
        - List of entities exposed by the ESPHome device.
        - Each entry describes one discovered entity.
    type: list
    elements: dict
    returned: always
    sample:
        - object_id: "snow_distance"
          key: 1
          name: "Snow Distance"
          type: "SensorInfo"
        - object_id: "snow_height"
          key: 2
          name: "Snow Height"
          type: "SensorInfo"
'''

from ansible.module_utils.basic import AnsibleModule
import aioesphomeapi
import asyncio
from typing import Optional

async def get_device_data(host: str, port: int = 6053, noise_psk: Optional[str] = None, password: Optional[str] = None):
    api = aioesphomeapi.APIClient(host, port, noise_psk=noise_psk, password=password)
    await api.connect(login=True)

    try:
        api_version = f"{api.api_version.major}.{api.api_version.minor}"
        device_info: DeviceInfo = await api.device_info()
        dev_info_dict = {
            "name": getattr(device_info, "name", None),
            "mac_address": getattr(device_info, "mac_address", None),
            "esphome_version": getattr(device_info, "esphome_version", None),
            "compilation_time": getattr(device_info, "compilation_time", None),
            "model": getattr(device_info, "model", None),
            "has_deep_sleep": getattr(device_info, "has_deep_sleep", None),
        }
        entities, services = await api.list_entities_services()
        entities_list = []
        for entity in entities:
            entities_list.append({
                "object_id": getattr(entity, "object_id", None),
                "key": getattr(entity, "key", None),
                "name": getattr(entity, "name", None),
                "type": entity.__class__.__name__
            })

        return {
            "api_version": api_version,
            "device_info": dev_info_dict,
            "entities": entities_list
        }
    finally:
        await api.disconnect()


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        host=dict(type='str', required=True),
        port=dict(type='int', required=False, default=6053),
        noise_psk=dict(type='str', required=False, default=None, no_log=True),
        password=dict(type='str', required=False, default=None, no_log=True)
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)
    host = module.params['host']
    port = module.params['port']
    noise_psk = module.params['noise_psk']
    password = module.params['password']

    try:
        result_data = asyncio.run(get_device_data(host, port, noise_psk, password))
        module.exit_json(changed=False, esphome_facts=result_data)

    except Exception as e:
        module.fail_json(msg=f"ESPHome communication error: {str(e)}")


def main():
    run_module()


if __name__ == '__main__':
    main()
