# Host srv-01: Proxmox VE — Lenovo M920x (Nodo Principal)

Nodo principal del clúster Proxmox, ejecutado sobre un **Lenovo ThinkStation M920x Tiny** con arquitectura **x86_64**. Usa Proxmox VE oficial sobre **Debian 13 Trixie** con repositorio `pve-no-subscription`. Es el nodo que creó el clúster al que se unió posteriormente `rp5-01`.

---

## 1. Hardware

| Componente | Detalle |
|---|---|
| **Máquina** | Lenovo ThinkStation M920x Tiny |
| **Arquitectura** | x86_64 |
| **CPU** | *(completar — ej. Intel Core i7-8700T)* |
| **RAM** | *(completar — ej. 32 GB DDR4)* |
| **Almacenamiento** | *(completar — ej. 512 GB NVMe + HDD)* |
| **Red** | Ethernet (ej. enp1s0) |
| **IP de gestión** | 192.168.1.11 |
| **Nodo en clúster** | `srv-01` |
| **Kernel** | 7.0.2-2-pve (PMX, 2026-05-08) |

---

## 2. Sistema Operativo y Proxmox VE

Proxmox VE instalado desde ISO oficial sobre **Debian 13 Trixie**, con repositorio gratuito `pve-no-subscription` (sin licencia de pago).

### Repositorio

```bash
# Eliminar el repo enterprise (requiere suscripción)
rm /etc/apt/sources.list.d/pve-enterprise.list

# Añadir repositorio gratuito
cat > /etc/apt/sources.list.d/pve-no-subscription.list << 'EOF'
deb http://download.proxmox.com/debian/pve trixie pve-no-subscription
EOF

# Actualizar sistema completo
apt update && apt dist-upgrade -y
```

> El repositorio `pve-no-subscription` es funcional y recibe actualizaciones de seguridad. La única diferencia respecto al Enterprise es la ausencia de SLA y soporte comercial.

---

## 3. Configuración de Red

### `/etc/network/interfaces`

```
auto lo
iface lo inet loopback

auto enp1s0
iface enp1s0 inet manual

auto vmbr0
iface vmbr0 inet static
    address 192.168.1.11/24
    gateway 192.168.1.1
    dns-nameservers 192.168.1.20
    bridge-ports enp1s0
    bridge-stp off
    bridge-fd 0
```

> `vmbr0` es el bridge al que se conectan todos los contenedores y VMs. El nombre del interfaz físico puede variar (`enp1s0`, `eth0`, etc.) — verificar con `ip link show`.

### `/etc/hosts`

```
127.0.0.1       localhost
192.168.1.11    srv-01.dap.gal srv-01
```

---

## 4. NTP (Chrony)

```bash
apt install -y chrony
systemctl enable chrony
systemctl start chrony

# Verificar sincronización
chronyc tracking
chronyc sources
```

---

## 5. Creación del Clúster

`srv-01` es el nodo que inicializó el clúster. `rp5-01` se unió posteriormente.

```bash
# Crear el clúster (ejecutar una sola vez en el nodo principal)
pvecm create homelab

# Verificar estado
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

---

## 6. Módulo FUSE (para contenedores con Ollama / nesting)

```bash
# Cargar el módulo fuse inmediatamente
modprobe fuse

# Persistir en reinicios
echo "fuse" >> /etc/modules
```

> Necesario para el CT 143 (y cualquier otro que use `nesting=1` o montajes FUSE internos, como Ollama).

---

## 7. Configuración de Contenedores Especiales

### CT 143 — Nesting habilitado

```bash
# Habilitar nesting (necesario para contenedores que corren Docker u Ollama)
pct set 143 --features nesting=1
pct restart 143
```

Edición manual del fichero de configuración si es necesario:

```bash
nano /etc/pve/lxc/143.conf
```

---

## 8. Hardening SSH

```bash
cat >> /etc/ssh/sshd_config << 'EOF'
PermitRootLogin prohibit-password
PasswordAuthentication no
MaxAuthTries 3
EOF

systemctl reload sshd
```

> El acceso directo a este nodo desde fuera de la LAN debe hacerse saltando por el bastión `rp5-01-ct-ssh` (192.168.1.21).

---

## 9. Monitorización

### Node Exporter

```bash
apt install -y prometheus-node-exporter
systemctl enable prometheus-node-exporter
systemctl start prometheus-node-exporter
```

Expone métricas del host en `http://192.168.1.11:9100/metrics`.

### Glances (monitorización interactiva local)

```bash
apt install -y glances

# Uso interactivo
glances

# Modo servidor web (opcional)
glances -w   # http://192.168.1.11:61208
```

---

## 10. Contenedores Alojados

| CT ID | Nombre | IP | Descripción |
|---|---|---|---|
| 1XX | srv-01-ct-proxy | 192.168.1.31 | Traefik — Reverse proxy |
| 1XX | srv-01-ct-tunnel | 192.168.1.XX | Cloudflare Tunnel |
| 1XX | srv-01-ct-whost | 192.168.1.40 | nginx — Web hosting dap.gal |
| 143 | srv-01-ct-sudofeed | 192.168.1.98 | Bot publicación automatizada |

---

## 11. Almacenamiento

```bash
# Ver dispositivos físicos
lsblk
fdisk -l

# Ver uso actual
df -h

# Ver pools configurados en Proxmox
pvesm status
```

Configuración de almacenamiento en `/etc/pve/storage.cfg` (gestionada desde la UI del clúster).

---

## 12. Backups (vzdump)

Configurar desde **Datacenter → Backup** en la UI, o manualmente:

```bash
# Backup manual de un CT (comprimido, a almacenamiento local)
vzdump <CTID> --compress zstd --storage local

# Backup de todos los CTs del nodo
vzdump --all --compress zstd --storage local
```

> Recomendado: programar backup nocturno semanal desde la UI de Proxmox.

---

## 13. Comandos Útiles

```bash
# Estado del clúster
pvecm status
pvecm nodes

# Listar todos los CTs del nodo
pct list

# Arrancar / parar / reiniciar un CT
pct start <CTID>
pct stop <CTID>
pct restart <CTID>

# Entrar a la consola de un CT
pct enter <CTID>

# Estado de servicios Proxmox
systemctl list-units 'pve*' 'corosync*'

# Ver configuración de un CT
cat /etc/pve/lxc/<CTID>.conf

# Logs del clúster
journalctl -u pve-cluster -n 50 --no-pager
journalctl -u corosync -n 50 --no-pager

# Sincronización NTP
chronyc tracking

# Uso de recursos
top
glances

# Node Exporter
curl -s http://localhost:9100/metrics | grep node_load
```

---

## 14. Acceso a la UI de Proxmox

| URL | Descripción |
|---|---|
| `https://192.168.1.11:8006` | Interfaz web principal (este nodo) |
| `https://192.168.1.XX:8006` | Nodo rp5-01 (vista del mismo clúster) |

> Credenciales: usuario `root`, autenticación PAM. Accesible solo desde la LAN.

---

## 15. Lo que falta documentar / configurar

### Pendiente de documentar
- **Especificaciones exactas de hardware** (CPU, RAM, disco) del M920x
- **IP del nodo rp5-01** y los IDs de CT de todos los contenedores
- **Interfaz de red física** (`enp1s0` u otro — verificar con `ip link show`)
- **CT 143** — confirmar a qué servicio corresponde (presumiblemente `srv-01-ct-sudofeed`)

### Pendiente de configurar
- **Backups automáticos** — no hay ningún schedule configurado; riesgo de pérdida de datos ante fallo de disco
- **Alertas de monitorización** — Grafana no tiene alertas configuradas si Proxmox o un CT cae
- **Firewall de Proxmox** — el firewall a nivel de datacenter/nodo está desactivado; toda la seguridad recae en UFW dentro de cada CT
- **Actualizaciones automáticas** — no hay `unattended-upgrades` ni cron de `apt upgrade` en el host
- **SMART monitoring** — no hay monitorización del estado de los discos físicos (`smartmontools`)
- **Notificaciones** — sin alertas por email ni Telegram si un servicio cae o el disco llega al límite