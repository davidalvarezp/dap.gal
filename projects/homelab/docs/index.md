# Homelab

## Hardware

| Hostname        | IP                            | Especificaciones                                              |
|-----------------|-------------------------------|---------------------------------------------------------------|
| **rt-01**       | 192.168.1.254 / 10.0.10.1     | TP-Link TL-R605                                               |
| **sw-01**       | 10.0.10.254                   | Netgear GS308Lv4                                              |
| **rp-01**       | 10.0.10.10                    | Raspberry Pi 5 8GB + M.2 Hat + 128GB NVME                     |
| **sv-01**       | 10.0.10.11                    | Lenovo m920x - i3 16GB 256GB NVME 1TB SSD                     |
| **sv-02**       | 10.0.10.12                    | Lenovo m920x - i3 16GB 256GB NVME                             |
| **sv-03**       | 10.0.10.13                    | Custom - Ryzen 5 5400G 16GB 3200Mhz 256GB NVME                |



## Diseño

Router: TP-Link TL-R605
Switch: Netgear GS308Lv4

vlanes:
    vlan10 (lan/infraestructura): 10.0.10.0/24
    vlan20 (servicios locales): 10.0.20.0/24
    vlan40 (dmz/servicios expuestos): 10.0.40.0/24

router:
  - WAN 192.168.1.254
  - vlan_lan 10.0.10.1
  - vlan_loc 10.0.20.1
  - vlan_dmz 10.0.40.1


switch 10.0.10.254 (con a router)

rp-01 10.0.10.10 (con a router)
  - ct-dns      10.0.10.101 (pi-hole)
  - ct-ssh      10.0.10.105 (bastion)

sv-01 10.0.10.11 (con a switch)
  - ct-homep    10.0.20.51 (homepage)
  - ct-stats    10.0.20.52 (prometheus+grafana)
  - ct-n8n      10.0.20.53 (n8n)
  - ct-smb      10.0.20.101 (samba)
  - ct-cloud    10.0.20.102 (nextcloud)
  - ct-photo    10.0.20.103 (immich)

sv-02 10.0.10.12
  - ct-proxy    10.0.40.50 (traefik)
  - ct-whost    10.0.40.51 (nginx)
  - ct-webai    10.0.40.52 (openwebui)
  - ct-mc       10.0.40.100 (minegraft server)

sv-03 10.0.10.13
  - llamma.pp local 10.0.20.13


## Reglas Router

### VLAN10
  - Acceso total.

### VLAN20
  - Acceso a internet
  - Acceso a DNS 10.0.10.101

### VLAN40
  - Acceso a internet
  - Acceso a DNS 10.0.10.101
  - Acceso a LLM 10.0.20.13