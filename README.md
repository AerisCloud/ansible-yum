Yum
===

Because the speed of execution of the original [yum module](https://github.com/ansible/ansible-modules-core/blob/devel/packaging/os/yum.py), shipped with ansible,
is extremely slow, we have written a new module faster, which uses the same commands, you would use if you try to install a package manually.

This module is written is python, but the logic is inspired from the [yum2 shell module](https://github.com/rhaido/ansible-modules/blob/master/yum2).

We choose to call it `yum` to be able to use the [`with_items` *hacks*](https://github.com/ansible/ansible/blob/devel/lib/ansible/runner/__init__.py#L751).
It means, that when you use `with_items` with the `yum` module, instead of calling the module one time for each item, it will call it once, with all the items as one argument.

It supports most of the options supported by the [original yum module](http://docs.ansible.com/yum_module.html),
however the `list` option is not supported.

Usage
-----

In your role's meta, add a dependency to this role using the syntax described below.

```yaml
# my_role/meta/main.yml
dependencies:
  - role: aeriscloud.yum
```

See also
--------

* [Official yum module documentation](http://docs.ansible.com/yum_module.html)
* [Yum2 on GitHub](https://github.com/rhaido/ansible-modules/blob/master/yum2)
* [New and Fast Module for Ansible: yum2](http://blog.grozak.com/2014/04/04/01-yum2-ansible-module/)
