#!/usr/bin/python

# Copyright: (c) 2026, Ondřej Ježek
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


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


def get_nameserver(module, api_key, name):
    url = "https://api.netbird.io/api/dns/nameservers"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Token {api_key}'
    }
    response, info = fetch_url(module, url, headers=headers)
    if info['status'] == 200:
        nameservers = json.loads(response.read())
        for ns in nameservers:
            if ns['name'] == name:
                return ns
        return None
    else:
        raise Exception(f"Failed to get nameservers: {info['status']} - {info['body']}")


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


def create_nameserver_group(module, api_key, name, description, nameservers, enabled, group_ids, primary, domains, search_domains_enabled):
    url = "https://api.netbird.io/api/dns/nameservers"
    payload = json.dumps({
        "name": name,
        "description": description,
        "nameservers": nameservers,
        "enabled": enabled,
        "groups": group_ids,
        "primary": primary,
        "domains": domains,
        "search_domains_enabled": search_domains_enabled
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
        raise Exception(f"Failed to create nameserver group: {info['status']} - {info['body']}")


def update_nameserver_group(module, api_key, nameserver_group_id, name, description, nameservers, enabled, group_ids, primary, domains, search_domains_enabled):
    url = f"https://api.netbird.io/api/dns/nameservers/{nameserver_group_id}"
    payload = json.dumps({
        "name": name,
        "description": description,
        "nameservers": nameservers,
        "enabled": enabled,
        "groups": group_ids,
        "primary": primary,
        "domains": domains,
        "search_domains_enabled": search_domains_enabled
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
        raise Exception(f"Failed to update nameserver group: {info['status']} - {info['body']}")


def run_module():
    module_args = dict(
        api_key=dict(type='str', required=True),
        name=dict(type='str', required=True),
        description=dict(type='str', default=''),
        nameservers=dict(type='list', required=True, elements='dict',
                         options=dict(
                             ip=dict(type='str', required=True),
                             ns_type=dict(type='str', default='udp'),
                             port=dict(type='int', default=53)
                         )),
        enabled=dict(type='bool', default=True),
        groups=dict(type='list', elements='str', required=True),
        primary=dict(type='bool', default=True),
        domains=dict(type='list', elements='str', default=[]),
        search_domains_enabled=dict(type='bool', default=False)
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
    name = module.params['name']
    description = module.params['description']
    nameservers = module.params['nameservers']
    enabled = module.params['enabled']
    group_names = module.params['groups']
    primary = module.params['primary']
    domains = module.params['domains']
    search_domains_enabled = module.params['search_domains_enabled']

    try:
        nameserver_group = get_nameserver(module, api_key, name)
        group_ids = find_group_ids(module, api_key, group_names)
    except Exception as err:
        module.fail_json(msg=str(err), **result)
        return

    if module.check_mode:
        result['message'] = "Would create nameserver group" if not nameserver_group else "Would update nameserver group"
        module.exit_json(**result)

    if not nameserver_group:
        try:
            create_nameserver_group(module, api_key, name, description, nameservers, enabled, group_ids, primary, domains, search_domains_enabled)
        except Exception as err:
            module.fail_json(msg=str(err), **result)
            return
        result['message'] = "Nameserver group created"
        result['changed'] = True
    else:
        if (nameserver_group['description'] != description or
            nameserver_group['nameservers'] != nameservers or
            nameserver_group['enabled'] != enabled or
            set(nameserver_group['groups']) != set(group_ids) or
            nameserver_group['primary'] != primary or
            nameserver_group['domains'] != domains or
            nameserver_group['search_domains_enabled'] != search_domains_enabled):

            try:
                update_nameserver_group(module, api_key, nameserver_group['id'], name, description, nameservers, enabled, group_ids, primary, domains, search_domains_enabled)
            except Exception as err:
                module.fail_json(msg=str(err), **result)
                return
            result['message'] = "Nameserver group updated"
            result['changed'] = True
        else:
            result['message'] = "Nameserver group already exists and is up to date"
            result['changed'] = False

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()