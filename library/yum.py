#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = '''
---
module: yum
short_description: Manages packages with the I(yum) package manager
description:
     - Installs, upgrade, removes, and lists packages and groups with the I(yum) package manager.
options:
  name:
    description:
      - "Package name, or package specifier with version, like C(name-1.0). When using state=latest, this can be '*' which means run: yum -y update. You can also pass a url or a local path to a rpm file."
    required: true
    default: null
    aliases: []
  state:
    description:
      - Whether to install (C(present), C(latest)), or remove (C(absent)) a package.
    required: false
    choices: [ "present", "latest", "absent" ]
    default: "present"
  enablerepo:
    description:
      - I(Repoid) of repositories to enable for the install/update operation.
        These repos will not persist beyond the transaction.
        When specifying multiple repos, separate them with a ",".
    required: false
    default: null
    aliases: []
  disablerepo:
    description:
      - I(Repoid) of repositories to disable for the install/update operation.
        These repos will not persist beyond the transaction.
        When specifying multiple repos, separate them with a ",".
    required: false
    default: null
    aliases: []
  conf_file:
    description:
      - The remote yum configuration file to use for the transaction.
    required: false
    default: null
    aliases: []
  disable_gpg_check:
    description:
      - Whether to disable the GPG checking of signatures of packages being
        installed. Has an effect only if state is I(present) or I(latest).
    required: false
    default: "no"
    choices: ["yes", "no"]
    aliases: []
  update_cache:
    description:
      - Force updating the cache. Has an effect only if state is I(present)
        or I(latest).
    required: false
    default: "no"
    choices: ["yes", "no"]
    aliases: []

notes: []
# informational: requirements for nodes
requirements: [ yum ]
author: Emilien Kenler
'''

EXAMPLES = '''
- name: install the latest version of Apache
  yum: name=httpd state=latest
- name: remove the Apache package
  yum: name=httpd state=absent
- name: install the latest version of Apache from the testing repo
  yum: name=httpd enablerepo=testing state=present
- name: install one specific version of Apache
  yum: name=httpd-2.2.29-1.4.amzn1 state=present
- name: upgrade all packages
  yum: name=* state=latest
- name: install the nginx rpm from a remote repo
  yum: name=http://nginx.org/packages/centos/6/noarch/RPMS/nginx-release-centos-6-0.el6.ngx.noarch.rpm state=present
- name: install nginx rpm from a local file
  yum: name=/usr/local/src/nginx-release-centos-6-0.el6.ngx.noarch.rpm state=present
- name: install the 'Development tools' package group
  yum: name="@Development tools" state=present
'''

import os

from ansible.module_utils.basic import *

module = AnsibleModule(
    argument_spec=dict(
        package=dict(required=True, aliases=['pkg', 'name'], type='list'),
        # removed==absent, installed==present, these are accepted as aliases
        state=dict(default='installed',
                   choices=['absent', 'present', 'installed', 'removed',
                            'latest']),
        enablerepo=dict(),
        disablerepo=dict(),
        conf_file=dict(default=None),
        disable_gpg_check=dict(required=False, default="no", type='bool'),
        update_cache=dict(required=False, default="no", type='bool'),
    )
)


def is_installed(name):
    rc, _, _ = module.run_command(['rpmquery', '--quiet', name])
    return rc == 0


def get_version(name):
    if is_installed(name):
        _, out, _ = module.run_command(' '.join(['rpmquery',
                                        '--queryformat="%{VERSION}-%{RELEASE}"',
                                        name]), check_rc=True)
        return out
    else:
        _, out, _ = module.run_command(' '.join(['rpmquery',
                                        '--whatprovides',
                                        '--queryformat="%{VERSION}-%{RELEASE}"',
                                        name]), check_rc=True)
        return out


def main():
    packages = module.params['package']
    state = module.params['state']
    if state == 'removed':
        state = 'absent'
    elif state == 'installed':
        state = 'present'

    cmd = "yum -q -y"
    changed = False

    if module.params['enablerepo'] and state != 'absent':
        cmd += " --enablerepo={0}".format(module.params['enablerepo'])
    if module.params['disablerepo'] and state != 'absent':
        cmd += " --disablerepo={0}".format(module.params['disablerepo'])
    if module.params['disable_gpg_check']:
        cmd += " --nogpgcheck"

    conf_file = module.params['conf_file']
    if conf_file and os.path.exists(conf_file):
        cmd += " -c " + conf_file

    if state in ['present', 'latest']:
        if module.params['update_cache']:
            module.run_command(cmd + " makecache")

    to_install = []
    to_update = []
    to_remove = []

    if state == 'present':
        for pkg in packages:
            if pkg.endswith('.rpm'):
                _, real_name, _ = module.run_command(
                    [
                        'rpm', '-q',
                        '--queryformat',
                        '%{NAME}-%{VERSION}-%{RELEASE}.%{ARCH}',
                        '-p', pkg
                    ], check_rc=True)
                if not is_installed(real_name):
                    to_install.append(pkg)
            else:
                if not is_installed(pkg):
                    to_install.append(pkg)

    elif state == 'latest':
        for pkg in packages:
            if not is_installed(pkg):
                to_install.append(pkg)
            else:
                to_update.append(pkg)
    elif state == 'absent':
        for pkg in packages:
            if is_installed(pkg):
                to_remove.append(pkg)

    if to_install:
        module.run_command(cmd + ' install ' + ' '.join(to_install),
                           check_rc=True)
        changed = True

    if to_update:
        old = get_version(' '.join(to_update))
        module.run_command(cmd + ' update ' + ' '.join(to_update),
                           check_rc=True)
        new = get_version(' '.join(to_update))
        if old != new:
            changed = True

    if to_remove:
        module.run_command(cmd + ' remove ' + ' '.join(to_remove),
                           check_rc=True)
        changed = True

    module.exit_json(msg='OK', changed=changed)


main()
