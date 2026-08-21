# ct-dns - config

Contenido del archivo `/var/lib/lxc/ct-dns/config`:

```conf
# Template used to create this container: /usr/share/lxc/templates/lxc-download
# Parameters passed to the template: -d debian -r bookworm -a arm64
# For additional config options, please look at lxc.container.conf(5)

# Uncomment the following line to support nesting containers:
#lxc.include = /usr/share/lxc/config/nesting.conf
# (Be aware this has security implications)


# Distribution configuration
lxc.include = /usr/share/lxc/config/common.conf
lxc.arch = linux64

# Container specific configuration
#! lxc.apparmor.profile = generated
#!lxc.apparmor.allow_nesting = 1
lxc.rootfs.path = dir:/var/lib/lxc/ct-dns/rootfs
lxc.uts.name = ct-dns

# Start config
lxc.start.auto = 1
lxc.start.order = 0
lxc.start.delay = 0

# System config
lxc.cgroup2.cpuset.cpus = 0-3
lxc.cgroup2.memory.max = 2048M
lxc.cgroup2.memory.swap.max = 512M
lxc.cgroup2.cpu.weight = 100

# Network config
lxc.net.0.type = veth
lxc.net.0.link = br0
lxc.net.0.flags = up
```