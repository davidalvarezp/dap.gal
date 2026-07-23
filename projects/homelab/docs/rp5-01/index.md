---
title: RP5-01
description: Nodo RP5-01 basado en Raspberry Pi 5 (8GB RAM, 128GB SSD). Infraestructura base del homelab.
---

# Host rp5-01: Proxmox VE — Raspberry Pi 5

Nodo secundario del clúster Proxmox, ejecutado sobre una **Raspberry Pi 5** con arquitectura **ARM64**. Corre Proxmox VE mediante el port comunitario **PXVIRT** (mirrors.lierfang.com), integrado en el clúster junto al nodo principal `srv-01` (M920x). Aloja los contenedores de la red `192.168.1.0/24` propios de la RPi.

---

## 1. Hardware

| Componente | Detalle |
|---|---|
| **Placa** | Raspberry Pi 5 |
| **Arquitectura** | ARM64 (aarch64) |
| **Almacenamiento** | NVMe (nvme0n1) vía HAT |
| **Red** | Ethernet (eth0) |
| **IP de gestión** | 192.168.1.XX *(completar)* |
| **Nodo en clúster** | `rp5-01` |

---

## 2. Sistema Operativo Base

Debian 12 Bookworm (ARM64) con Proxmox VE instalado desde el port comunitario PXVIRT, ya que Proxmox no ofrece soporte oficial para ARM64.

> **Nota:** Este nodo usa el mirror `mirrors.lierfang.com/pxcloud/pxvirt` en lugar de los repositorios oficiales de Proxmox, que solo soportan x86_64.

---

## 3. Instalación de Proxmox VE (ARM64)

### Repositorio PXVIRT

```bash
# GPG key del mirror
curl -L https://mirrors.lierfang.com/pxcloud/lierfang.gpg \
    -o /etc/apt/trusted.gpg.d/lierfang.gpg

# Repositorio (detecta automáticamente "trixie" como VERSION_CODENAME)
source /etc/os-release
echo "deb [arch=arm64] https://mirrors.lierfang.com/pxcloud/pxvirt $VERSION_CODENAME main" \
    > /etc/apt/sources.list.d/pxvirt-sources.list

apt update
```

### Paquetes

```bash
# Deshabilitar NetworkManager antes de instalar (conflicto con ifupdown2)
systemctl disable NetworkManager
systemctl stop NetworkManager
systemctl mask NetworkManager

# Red gestionada por ifupdown2
apt install -y ifupdown2
rm -f /etc/network/interfaces.new

# Proxmox VE completo
apt install -y proxmox-ve pve-manager qemu-server pve-cluster \
               postfix open-iscsi chrony

# Actualización completa tras instalación
apt update && apt dist-upgrade -y
```

---

## 4. Configuración de Red

### `/etc/network/interfaces`

```
auto lo
iface lo inet loopback

auto eth0
iface eth0 inet static
    address 192.168.1.XX/24
    gateway 192.168.1.1
    dns-nameservers 192.168.1.20
```

### `/etc/hosts`

```
127.0.0.1       localhost
192.168.1.XX    rp5-01.dap.gal rp5-01
```

### `/etc/hostname`

```
rp5-01
```

---

## 5. NTP (Chrony)

```bash
apt install -y chrony
systemctl enable chrony
systemctl start chrony

# Verificar sincronización
chronyc tracking
```

> La sincronización precisa es obligatoria para el clúster Proxmox (Corosync es sensible a la deriva de reloj).

---

## 6. Integración en el Clúster

El nodo `rp5-01` se une al clúster existente creado en `srv-01` (192.168.1.11).

```bash
# En rp5-01 — unirse al clúster de srv-01
pvecm add 192.168.1.11

# Verificar estado del clúster
pvecm status
pvecm nodes
```

```
# Salida esperada de pvecm nodes:
Membership information
──────────────────────
Nodeid  Votes  Name
     1      1  srv-01   (192.168.1.11)
     2      1  rp5-01   (192.168.1.XX)
```

### Servicios del clúster

```bash
# Arrancar y habilitar servicios HA
systemctl enable --now pvestatd
systemctl enable --now pve-ha-crm
systemctl enable --now pve-ha-lrm
```

---

## 7. Watchdog (Alta Disponibilidad)

Necesario para que el HA de Proxmox pueda forzar el reinicio del nodo en caso de fallo.

```bash
# Activar watchdog hardware en la RPi 5
echo "dtparam=watchdog=on" >> /boot/firmware/config.txt
reboot

# Verificar que el dispositivo está disponible tras el reinicio
ls -la /dev/watchdog*
# Debe aparecer /dev/watchdog o /dev/watchdog0

# Arrancar el LRM (Local Resource Manager) del HA
systemctl enable --now pve-ha-lrm
systemctl status pve-ha-lrm
```

---

## 8. Almacenamiento

El nodo dispone de un NVMe conectado vía HAT.

```bash
# Ver dispositivos
lsblk
fdisk -l /dev/nvme0n1

# Ver uso actual
df -h
```

Configuración del almacenamiento en `/etc/pve/storage.cfg` (gestionada desde la UI del clúster o editando directamente).

---

## 9. Template LXC ARM64

Los contenedores ARM64 requieren una plantilla específica, distinta a la de x86_64.

```bash
# Descargar template Debian 12 ARM64 (cloud image)
wget -O /var/lib/vz/template/cache/debian-12-bookworm-arm64-cloud.tar.xz \
    "https://github.com/oneclickvirt/lxc_arm_images/releases/download/debian/debian_12_bookworm_arm64_cloud.tar.xz"

# Verificar que está disponible
ls -lh /var/lib/vz/template/cache/
```

> Usar esta plantilla al crear contenedores desde la UI de Proxmox o con `pct create`.

---

## 10. Hardening SSH

```bash
# Desactivar login por contraseña, solo clave pública
cat >> /etc/ssh/sshd_config << 'EOF'
PermitRootLogin prohibit-password
PasswordAuthentication no
MaxAuthTries 3
EOF

systemctl reload sshd
```

> El acceso remoto al nodo se realiza preferentemente a través del bastión (`rp5-01-ct-ssh`, 192.168.1.21).

---

## 11. Monitorización

### Node Exporter

```bash
apt install -y prometheus-node-exporter
systemctl enable prometheus-node-exporter
systemctl start prometheus-node-exporter
```

Expone métricas del host en `http://192.168.1.XX:9100/metrics`.  
Prometheus las recoge automáticamente y Grafana las visualiza junto al resto de nodos del clúster.

### Glances (monitorización interactiva local)

```bash
apt install -y glances

# Uso interactivo en consola
glances

# Modo servidor web (opcional)
glances -w   # accesible en http://192.168.1.XX:61208
```

---

## 12. Contenedores Alojados

| CT | Nombre | IP | Descripción |
|---|---|---|---|
| CT 2XX | rp5-01-ct-dns | 192.168.1.20 | Pi-hole DNS |
| CT 2XX | rp5-01-ct-ssh | 192.168.1.21 | SSH Bastion + 2FA |

---

## 13. Comandos Útiles

```bash
# Estado del clúster
pvecm status
pvecm nodes

# Estado de servicios Proxmox
systemctl list-units 'pve*' 'corosync*'

# Ver todos los contenedores del nodo
pct list

# Estado de HA
pve-ha-crm status
systemctl status pve-ha-lrm

# Sincronización NTP
chronyc tracking
chronyc sources

# Uso de recursos
top
glances

# Temperatura de la RPi 5
cat /sys/class/thermal/thermal_zone0/temp   # dividir entre 1000 → ºC

# Logs del clúster
journalctl -u pve-cluster -n 50 --no-pager
journalctl -u corosync -n 50 --no-pager

# Estado Node Exporter
systemctl status prometheus-node-exporter
curl -s http://localhost:9100/metrics | grep node_load
```

---

## 14. Acceso a la UI de Proxmox

La interfaz web del clúster es accesible desde cualquiera de los nodos:

| URL | Nodo |
|---|---|
| `https://192.168.1.11:8006` | srv-01 (M920x) — nodo principal |
| `https://192.168.1.XX:8006` | rp5-01 (RPi 5) — este nodo |

> Ambas URLs muestran la vista completa del clúster con todos los nodos y contenedores.