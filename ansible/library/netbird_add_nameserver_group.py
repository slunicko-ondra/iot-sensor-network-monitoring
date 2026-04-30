#!/usr/bin/python

# Copyright: (c) 2026, Ondřej Ježek
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = r'''
---
module: netbird_add_nameserver_group

short_description: Manages Netbird DNS nameserver groups via REST API

version_added: "1.0.0"

description:
  - This module manages DNS nameserver group configurations in Netbird.
  - It can create new nameserver groups, update existing ones, or verify that they are configured correctly.
  - The module connects to the Netbird REST API and performs operations on DNS nameserver groups.
  - If a nameserver group with the specified name already exists, the module will update it if any parameters differ.
  - Supports idempotent operations and check mode for dry-run verification.

options:
    api_key:
        description:
            - Netbird API token for authentication.
            - This is required to authenticate with the Netbird REST API.
            - Can be obtained from the Netbird admin dashboard.
        required: true
        type: str
    
    name:
        description:
            - Name of the nameserver group.
            - Must be unique within the Netbird organization.
            - This is used to identify the nameserver group for creation or updates.
        required: true
        type: str
    
    description:
        description:
            - Description of the nameserver group.
            - Optional field for documentation purposes.
        required: false
        type: str
        default: ''
    
    nameservers:
        description:
            - List of DNS nameservers in this group.
            - Each nameserver is a dictionary containing IP address and optional configuration.
        required: true
        type: list
        elements: dict
        suboptions:
            ip:
                description:
                    - IP address of the DNS nameserver.
                    - Can be IPv4 or IPv6 address.
                required: true
                type: str
            ns_type:
                description:
                    - Protocol type for the nameserver.
                    - Use 'udp' for standard DNS or 'tcp' for TCP-based DNS.
                required: false
                type: str
                default: 'udp'
            port:
                description:
                    - Port number for the DNS nameserver.
                    - Default DNS port is 53.
                required: false
                type: int
                default: 53
    
    enabled:
        description:
            - Whether the nameserver group is enabled.
            - When disabled, the nameserver group is not used for DNS resolution.
        required: false
        type: bool
        default: true
    
    groups:
        description:
            - List of Netbird group names to which this nameserver group applies.
            - The nameserver group will be used for DNS resolution by members of these groups.
            - All specified groups must exist in the Netbird organization.
        required: true
        type: list
        elements: str
    
    primary:
        description:
            - Whether this nameserver group is primary.
            - Only one nameserver group per domain can be primary.
        required: false
        type: bool
        default: true
    
    domains:
        description:
            - List of domains to be resolved by this nameserver group.
            - When a domain is specified, DNS queries for that domain will be routed to these nameservers.
            - Leave empty to use these nameservers for all domains not covered by other groups.
        required: false
        type: list
        elements: str
        default: []
    
    search_domains_enabled:
        description:
            - Whether to enable search domain resolution.
            - When enabled, unqualified domain names will be searched using the configured domains.
        required: false
        type: bool
        default: false

author:
    - Ondřej Ježek

notes:
    - All times are in UTC and represented in ISO-8601 format
    - The module requires network connectivity to the Netbird API
    - Authentication is done via API token in the Authorization header
    - The module supports check mode (C(--check)) for preview operations

requirements:
    - Netbird account with API access
    - Valid Netbird API token
'''

EXAMPLES = r'''
# Create a basic nameserver group for Cloudflare DNS
- name: Create Cloudflare DNS nameserver group
  netbird_add_nameserver_group:
    api_key: "{{ netbird_api_token }}"
    name: "Cloudflare DNS"
    description: "Cloudflare public DNS servers"
    nameservers:
      - ip: "1.1.1.1"
        ns_type: "udp"
        port: 53
      - ip: "1.0.0.1"
        ns_type: "udp"
        port: 53
    groups:
      - "all_users"
    enabled: true
    primary: true
    domains: []
    search_domains_enabled: false

# Create a nameserver group for internal domain resolution
- name: Create internal DNS nameserver group
  netbird_add_nameserver_group:
    api_key: "{{ netbird_api_token }}"
    name: "Internal DNS"
    description: "DNS for internal network domains"
    nameservers:
      - ip: "192.168.1.1"
        ns_type: "udp"
        port: 53
      - ip: "192.168.1.2"
        ns_type: "udp"
        port: 53
    groups:
      - "internal_team"
      - "servers"
    enabled: true
    primary: true
    domains:
      - "internal.example.com"
      - "local"
    search_domains_enabled: true

# Create a nameserver group with custom port
- name: Create custom DNS nameserver group
  netbird_add_nameserver_group:
    api_key: "{{ netbird_api_token }}"
    name: "Custom DNS Service"
    description: "Custom DNS server with non-standard port"
    nameservers:
      - ip: "10.0.0.1"
        ns_type: "tcp"
        port: 5053
    groups:
      - "dns_users"
    enabled: true
    primary: false
    domains:
      - "special.domain.com"
    search_domains_enabled: false

# Update an existing nameserver group (idempotent operation)
- name: Update existing nameserver group
  netbird_add_nameserver_group:
    api_key: "{{ netbird_api_token }}"
    name: "Cloudflare DNS"
    description: "Updated Cloudflare DNS configuration"
    nameservers:
      - ip: "1.1.1.1"
        ns_type: "udp"
        port: 53
      - ip: "1.0.0.1"
        ns_type: "udp"
        port: 53
      - ip: "1.1.1.3"
        ns_type: "udp"
        port: 53
    groups:
      - "all_users"
      - "developers"
    enabled: true
    primary: true
    domains: []
    search_domains_enabled: false

# Disable a nameserver group
- name: Disable nameserver group
  netbird_add_nameserver_group:
    api_key: "{{ netbird_api_token }}"
    name: "Old DNS Service"
    description: "Deprecated DNS configuration"
    nameservers:
      - ip: "8.8.8.8"
    groups:
      - "legacy_users"
    enabled: false
    primary: false
'''

RETURN = r'''
changed:
    description:
        - Whether the nameserver group was created, updated, or already exists unchanged.
        - Returns C(true) if the nameserver group was created or updated.
        - Returns C(false) if the nameserver group already exists with the same configuration.
    type: bool
    returned: always
    sample: true

message:
    description:
        - Human-readable message describing what action was performed.
        - Messages can indicate creation, update, or that configuration is already up to date.
    type: str
    returned: always
    sample: "Nameserver group created"
    examples:
        - "Nameserver group created"
        - "Nameserver group updated"
        - "Nameserver group already exists and is up to date"
        - "Would create nameserver group"
        - "Would update nameserver group"

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
