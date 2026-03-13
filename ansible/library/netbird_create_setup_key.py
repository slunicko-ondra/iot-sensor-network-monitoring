#!/usr/bin/python

# Copyright: (c) 2026, Ondřej Ježek
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from pygments.lexer import default

DOCUMENTATION = r'''
---
module: netbird_add_dns_server

short_description: This module adds a DNS server via Netbird REST API.

version_added: "1.0.0"

description: This module connects to the Netbird REST API and adds a DNS server configuration if it does not exist.

options:
    name:
        description: This is the message to send to the test module.
        required: true
        type: str
    new:
        description:
            - Control to demo if the result of this module is changed or not.
            - Parameter description can be a list as well.
        required: false
        type: bool

author:
    - Ondřej Ježek
'''

EXAMPLES = r'''
# Pass in a message
- name: Test with a message
  my_namespace.my_collection.my_test:
    name: hello world

# pass in a message and have changed true
- name: Test with a message and changed output
  my_namespace.my_collection.my_test:
    name: hello world
    new: true

# fail the module
- name: Test failure of the module
  my_namespace.my_collection.my_test:
    name: fail me
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
original_message:
    description: The original name param that was passed in.
    type: str
    returned: always
    sample: 'hello world'
message:
    description: The output message that the test module generates.
    type: str
    returned: always
    sample: 'goodbye'
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