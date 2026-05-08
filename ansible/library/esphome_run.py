#!/usr/bin/python

# Copyright: (c) 2026, Ondřej Ježek
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = r'''
---
module: esphome_device_ota

short_description: Runs an ESPHome OTA update against a target device.

version_added: "1.0.0"

description:
  - Runs the local C(esphome run) command against a device and configuration file.
  - Intended for OTA updates of ESPHome devices from Ansible.
  - The module is a thin wrapper around the ESPHome CLI and does not talk to the device API directly.

options:
    host:
        description:
            - Hostname or IP address of the ESPHome device to target.
            - This value is passed to C(esphome run --device).
        required: true
        type: str
    config_path:
        description:
            - Path to the ESPHome configuration file on the Ansible controller.
            - The file must exist locally where the module is executed.
        required: false
        type: str

notes:
    - In check mode the module exits immediately with C(changed=false) and does not run ESPHome.
    - The command is executed with C(--no-logs) to avoid streaming device logs during OTA updates.
    - Command failures and missing binaries are reported via C(fail_json) together with captured output.

author:
    - Ondřej Ježek

requirements:
    - esphome CLI installed on the Ansible controller
'''

EXAMPLES = r'''
# Run an OTA update for a single ESPHome device
- name: Update snow sensor firmware
  esphome_device_ota:
    host: 10.0.10.30
    config_path: /home/ondrej/git_repos/iot-sensor-network-monitoring-agent/sensors/esphome/snow_sensor.yaml

# Run an OTA update for a device reachable by hostname
- name: Update greenhouse sensor firmware
  esphome_device_ota:
    host: greenhouse-sensor.local
    config_path: /srv/esphome/greenhouse_sensor.yaml
'''

RETURN = r'''
changed:
    description:
        - C(true) when the OTA command is executed successfully.
        - C(false) in check mode.
    type: bool
    returned: always
    sample: true

original_message:
    description:
        - Human-readable summary of the OTA action that was started.
    type: str
    returned: always
    sample: "OTA update initiated for device 10.0.10.30 with config /srv/esphome/snow_sensor.yaml."

message:
    description:
        - Human-readable result message.
        - Indicates success when the ESPHome command completes without errors.
    type: str
    returned: always
    sample: "OTA update completed successfully."

stdout:
    description:
        - Captured standard output from the ESPHome CLI.
    type: str
    returned: on success
    sample: "..."

stderr:
    description:
        - Captured standard error from the ESPHome CLI.
    type: str
    returned: on success
    sample: "..."
'''

from ansible.module_utils.basic import AnsibleModule
import subprocess
from typing import Dict, Any


def esphome_run(host: str, config_path: str) -> Dict[str, Any]:
    command = [
        'esphome',
        'run',
        config_path,
        '--device',
        host,
        '--no-logs'
    ]

    try:
        result = subprocess.run(command, check=False, text=True, capture_output=True)
        return {
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": "esphome command not found."
        }


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        host=dict(type='str', required=True),
        config_path=dict(type='str', required=True)
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(
            changed=False,
            original_message='',
            message=''
        )

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)
    host = module.params['host']
    config_path = module.params['config_path']

    result = esphome_run(host, config_path)

    if not result.get('success', False):
        module.fail_json(
            msg=f"ESPHome OTA update failed with exit code {result.get('return_code', 'unknown')}.",
            stdout=result.get('stdout', ''),
            stderr=result.get('stderr', ''),
        )

    module.exit_json(
        changed=True,
        original_message=f"OTA update initiated for device {host} with config {config_path}.",
        message="OTA update completed successfully.",
        stdout=result.get('stdout', ''),
        stderr=result.get('stderr', '')
    )


def main():
    run_module()


if __name__ == '__main__':
    main()
