#!/usr/bin/python

# Copyright: (c) 2026, Ondřej Ježek
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = r'''
---
module: netbird_create_setup_key

short_description: Creates Netbird setup keys for device enrollment via REST API

version_added: "1.0.0"

description:
  - This module creates setup keys in Netbird that are used to enroll new devices into the network.
  - Setup keys can be one-off (single-use) or reusable for multiple devices.
  - The module automatically randomizes the key name with a suffix to ensure uniqueness.
  - Keys can be configured with expiration time, usage limits, and automatic group assignments.
  - Supports ephemeral peers and extra DNS labels configuration.
  - Returns the generated setup key that can be used by clients to register with Netbird.

options:
    api_key:
        description:
            - Netbird API token for authentication.
            - This is required to authenticate with the Netbird REST API.
            - Can be obtained from the Netbird admin dashboard.
        required: true
        type: str
    
    name_prefix:
        description:
            - Prefix for the setup key name.
            - The module will append a random suffix to ensure uniqueness.
            - For example, 'sensor' will become 'sensor_abc123'.
        required: true
        type: str
    
    type:
        description:
            - Type of setup key.
            - C(one-off) keys can only be used once to enroll a single peer.
            - C(reusable) keys can be used multiple times to enroll multiple peers (up to usage_limit).
        required: false
        type: str
        choices:
            - one-off
            - reusable
        default: one-off
    
    expires_in:
        description:
            - Expiration time for the setup key in seconds.
            - After this time, the key will no longer work for new enrollments.
            - Default is 86400 seconds (24 hours).
            - Set to 0 for keys that never expire (not recommended).
        required: false
        type: int
        default: 86400
    
    auto_groups:
        description:
            - List of Netbird group names to automatically assign peers enrolled with this key.
            - Peers will be added to these groups upon successful enrollment.
            - All specified groups must exist in the Netbird organization.
        required: false
        type: list
        elements: str
        default: []
    
    usage_limit:
        description:
            - Maximum number of times this setup key can be used for enrollment.
            - For C(one-off) keys, this should typically be 1.
            - For C(reusable) keys, can be set higher for shared deployment scenarios.
            - Use 0 for unlimited usage (not recommended).
        required: false
        type: int
        default: 1
    
    ephemeral:
        description:
            - Whether peers enrolled with this key should be ephemeral.
            - Ephemeral peers are automatically removed when they disconnect.
            - Useful for temporary device connections or CI/CD environments.
        required: false
        type: bool
        default: false
    
    allow_extra_dns_labels:
        description:
            - Whether to allow extra DNS labels for peers enrolled with this key.
            - Enables support for special DNS naming conventions.
        required: false
        type: bool
        default: false

author:
    - Ondřej Ježek

notes:
    - The module always creates a new setup key with a randomized name suffix
    - Setup keys are returned in the result and should be stored securely
    - All times are in UTC and represented in seconds
    - The module requires network connectivity to the Netbird API
    - Authentication is done via API token in the Authorization header
    - The module supports check mode (C(--check)) for preview operations

requirements:
    - Netbird account with API access
    - Valid Netbird API token
    - Target groups must exist before being assigned via auto_groups
'''

EXAMPLES = r'''
# Create a simple one-off setup key for a single sensor device
- name: Create one-off setup key for sensor
  netbird_create_setup_key:
    api_key: "{{ netbird_api_token }}"
    name_prefix: "sensor_enrollment"
    type: "one-off"
    expires_in: 86400
    auto_groups:
      - "sensors"
    usage_limit: 1
    ephemeral: false
    allow_extra_dns_labels: false
  register: setup_key_result

# Create a reusable setup key for multiple servers
- name: Create reusable setup key for server deployment
  netbird_create_setup_key:
    api_key: "{{ netbird_api_token }}"
    name_prefix: "server_deployment"
    type: "reusable"
    expires_in: 604800  # 7 days
    auto_groups:
      - "servers"
      - "monitoring"
    usage_limit: 5
    ephemeral: false
    allow_extra_dns_labels: false

# Create an ephemeral setup key for temporary CI/CD environments
- name: Create ephemeral setup key for CI/CD
  netbird_create_setup_key:
    api_key: "{{ netbird_api_token }}"
    name_prefix: "ci_cd_runner"
    type: "one-off"
    expires_in: 3600  # 1 hour
    auto_groups:
      - "ci_runners"
    usage_limit: 1
    ephemeral: true
    allow_extra_dns_labels: false

# Create a setup key that never expires (long-lived)
- name: Create long-lived reusable setup key
  netbird_create_setup_key:
    api_key: "{{ netbird_api_token }}"
    name_prefix: "iot_devices"
    type: "reusable"
    expires_in: 31536000  # 1 year
    auto_groups:
      - "iot_network"
    usage_limit: 100
    ephemeral: false
    allow_extra_dns_labels: true

# Create setup key and use the returned key for distribution
- name: Create setup key and save it
  netbird_create_setup_key:
    api_key: "{{ netbird_api_token }}"
    name_prefix: "field_devices"
    type: "one-off"
    expires_in: 172800  # 2 days
    auto_groups:
      - "field_team"
    usage_limit: 1
    ephemeral: false
  register: field_setup_key

- name: Display setup key for distribution
  debug:
    msg: "Setup key for field devices: {{ field_setup_key.key }}"
'''

RETURN = r'''
changed:
    description:
        - Whether the setup key was successfully created.
        - Returns C(true) when a new setup key is created.
        - Returns C(false) in check mode.
    type: bool
    returned: always
    sample: true

key:
    description:
        - The generated setup key string.
        - This key is used by devices to enroll with the Netbird network.
        - The key should be securely distributed to devices or users requiring enrollment.
        - Each setup key is unique and generated by the Netbird API.
    type: str
    returned: on success
    sample: "NhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MTcyMjQ..."

message:
    description:
        - Human-readable message describing the operation result.
        - In check mode, indicates what would be created.
        - On success, includes the generated setup key.
    type: str
    returned: always
    sample: "Setup key created successfully with key: NhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    examples:
        - "Setup key created successfully with key: ..."
        - "Would create setup key"

original_message:
    description:
        - Reserved field for future use, currently always empty.
    type: str
    returned: always
    sample: ''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url
import json
import random
import string


def get_setup_key(module, api_key, name):
    url = "https://api.netbird.io/api/setup-keys"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Token {api_key}'
    }
    response, info = fetch_url(module, url, headers=headers)
    if info['status'] == 200:
        setup_keys = json.loads(response.read())
        for key in setup_keys:
            if key['name'] == name:
                return key
        return None
    else:
        raise Exception(f"Failed to get setup keys: {info['status']} - {info['body']}")


def get_setup_key_id(module, api_key, name):
    setup_key = get_setup_key(module, api_key, name)
    return setup_key['id'] if setup_key else None


def find_group_ids(module, api_key, group_names):
    url = "https://api.netbird.io/api/groups"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Token {api_key}'
    }

    response, info = fetch_url(module, url, headers=headers)
    if info['status'] == 200:
        groups = json.loads(response.read())
        group_ids = []
        for group in groups:
            if group['name'] in group_names:
                group_ids.append(group['id'])
        if len(group_ids) != len(group_names):
            missing_groups = set(group_names) - set([group['name'] for group in groups])
            raise Exception(f"Groups not found: {', '.join(missing_groups)}")
        return group_ids
    else:
        raise Exception(f"Failed to get groups: {info['status']} - {info['body']}")


def create_setup_key(module, api_key, name, key_type, expires_in, auto_groups_ids, usage_limit, ephemeral=False, allow_extra_dns_labels=False):
    url = "https://api.netbird.io/api/setup-keys"
    payload = json.dumps({
        "name": name,
        "type": key_type,
        "expires_in": expires_in,
        "auto_groups": auto_groups_ids,
        "usage_limit": usage_limit,
        "ephemeral": ephemeral,
        "allow_extra_dns_labels": allow_extra_dns_labels
    })
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Token {api_key}'
    }
    response, info = fetch_url(module, url, method="POST", headers=headers, data=payload)
    if info['status'] in (200, 201):
        return json.loads(response.read())
    else:
        raise Exception(f"Failed to create setup key: {info['status']} - {info['body']}")


def update_setup_key(module, api_key, key_id, revoked, auto_groups_ids):
    url = f"https://api.netbird.io/api/setup-keys/{key_id}"
    payload = json.dumps({
        "revoked": revoked,
        "auto_groups": auto_groups_ids
    })
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Token {api_key}'
    }
    response, info = fetch_url(module, url, method="PUT", headers=headers, data=payload)
    if info['status'] == 200:
        return json.loads(response.read())
    else:
        raise Exception(f"Failed to update setup key: {info['status']} - {info['body']}")


def delete_setup_key(module, api_key, key_id):
    url = f"https://api.netbird.io/api/setup-keys/{key_id}"
    headers = {
        'Authorization': f'Token {api_key}'
    }
    response, info = fetch_url(module, url, method="DELETE", headers=headers)
    if info['status'] in (200, 204):
        return True
    else:
        raise Exception(f"Failed to delete setup key: {info['status']} - {info['body']}")


def randomize_setup_key_name(name_prefix):
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{name_prefix}_{random_suffix}"


def run_module():
    module_args = dict(
        api_key=dict(type='str', required=True),
        name_prefix=dict(type='str', required=True),
        type=dict(type='str', choices=['one-off', 'reusable'], default='one-off'),
        expires_in=dict(type='int', default=86400),
        auto_groups=dict(type='list', elements='str', default=[]),
        usage_limit=dict(type='int', default=1),
        ephemeral=dict(type='bool', default=False),
        allow_extra_dns_labels=dict(type='bool', default=False)
    )

    result = dict(
        changed=False,
        original_message='',
        message=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    api_key = module.params['api_key']
    name_prefix = module.params['name_prefix']
    key_type = module.params['type']
    expires_in = module.params['expires_in']
    auto_groups = module.params['auto_groups']
    usage_limit = module.params['usage_limit']
    ephemeral = module.params['ephemeral']
    allow_extra_dns_labels = module.params['allow_extra_dns_labels']

    if module.check_mode:
        result['message'] = "Would create setup key"
        module.exit_json(**result)

    try:
        group_ids = find_group_ids(module, api_key, auto_groups)
        create_response = create_setup_key(module, api_key, randomize_setup_key_name(name_prefix), key_type, expires_in,
                                           group_ids, usage_limit, ephemeral, allow_extra_dns_labels)
    except Exception as err:
        module.fail_json(msg=str(err), **result)
        return

    key = create_response['key'] if 'key' in create_response else None
    if not key:
        module.fail_json(msg="Failed to retrieve setup key from response", **result)
        return

    result['key'] = key
    result['message'] = f"Setup key created successfully with key: {key}"
    result['changed'] = True

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
