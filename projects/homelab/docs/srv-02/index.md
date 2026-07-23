# Host srv-02: Proxmox VE — Lenovo M920x (Nodo Secundario)

Nodo secundario del clúster Proxmox, ejecutado sobre un **Lenovo ThinkStation M920x Tiny** con arquitectura **x86_64**. Configuración idéntica a `srv-01` en cuanto a sistema base, con distinto conjunto de contenedores. Usa Proxmox VE oficial sobre **Debian 13 Trixie** con repositorio `pve-no-subscription` e integrado en el mismo clúster con HA habilitado.

---

## 1. Hardware

| Componente | Detalle |
|---|---|
| **Máquina** | Lenovo ThinkStation M920x Tiny |
| **Arquitectura** | x86_64 |
| **CPU** | *(completar — ej. Intel Core i7-8700T)* |
| **RAM** | *(completar — ej. 32 GB DDR4)* |
| **Almacenamiento** | *(completar — ej. 512 GB NVMe)* |
| **Red** | Ethernet *(completar — ej. enp1s0)* |
| **IP de gestión** | 192.168.1.XX *(completar)* |
| **Nodo en clúster** | `srv-02` |
| **Kernel** | 7.0.2-2-pve (PMX, 2026-05-08) |

---

## 2. Sistema Operativo y Proxmox VE

Proxmox VE instalado desde ISO oficial sobre **Debian 13 Trixie**, con repositorio gratuito `pve-no-subscription`.

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
    address 192.168.1.XX/24
    gateway 192.168.1.1
    dns-nameservers 192.168.1.20
    bridge-ports enp1s0
    bridge-stp off
    bridge-fd 0
```

### `/etc/hosts`

```
127.0.0.1       localhost
192.168.1.XX    srv-02.dap.gal srv-02
```

---

## 4. Integración en el Clúster

`srv-02` se une al clúster creado en `srv-01`.

```bash
# Unirse al clúster (ejecutar una sola vez)
pvecm add 192.168.1.11

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
     2      1  srv-02   (192.168.1.XX)
     3      1  rp5-01   (192.168.1.XX)
```

---

## 5. NTP (Chrony)

```bash
apt install -y chrony
systemctl enable chrony
systemctl start chrony

# Verificar sincronización
chronyc tracking
chronyc sources
```

---

## 6. Hardening SSH

```bash
cat >> /etc/ssh/sshd_config << 'EOF'
PermitRootLogin prohibit-password
PasswordAuthentication no
MaxAuthTries 3
EOF

systemctl reload sshd
```

> El acceso directo desde fuera de la LAN se realiza saltando por el bastión `rp5-01-ct-ssh` (192.168.1.21).

---

## 7. Alta Disponibilidad (HA)

El nodo participa en el HA del clúster. Estado verificable con:

```bash
ha-manager status
```

Para gestionar recursos HA:

```bash
# Ver recursos gestionados por HA
ha-manager config

# Añadir un CT al HA
ha-manager add ct:<CTID> --state started --group <grupo>

# Ver grupos HA definidos
ha-manager groupconfig
```

---

## 8. Gestión de Almacenamiento de CTs

```bash
# Redimensionar disco de un CT (ejemplo: CT 198, rootfs a 20 GB)
pct resize 198 rootfs 20G

# Ver uso de disco de un CT
pct df <CTID>

# Ver todos los volúmenes
pvesm list local
```

---

## 9. Monitorización

### Node Exporter

```bash
apt install -y prometheus-node-exporter
systemctl enable prometheus-node-exporter
systemctl start prometheus-node-exporter
```

Expone métricas del host en `http://192.168.1.XX:9100/metrics`.

### Glances (monitorización interactiva local)

```bash
apt install -y glances

# Uso interactivo
glances

# Modo servidor web (opcional)
glances -w   # http://192.168.1.XX:61208
```

---

## 10. Contenedores Alojados

| CT ID | Nombre | IP | Descripción |
|---|---|---|---|
| 198 | *(completar)* | 192.168.1.XX | *(completar)* |
| *(completar)* | *(completar)* | 192.168.1.XX | *(completar)* |

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

---

## 12. Backups (vzdump)

```bash
# Backup manual de un CT (comprimido, a almacenamiento local)
vzdump <CTID> --compress zstd --storage local

# Backup de todos los CTs del nodo
vzdump --all --compress zstd --storage local
```

> Recomendado: programar backup nocturno semanal desde **Datacenter → Backup** en la UI de Proxmox.

---

## 13. Comandos Útiles

```bash
# Estado del clúster
pvecm status
pvecm nodes

# Estado de HA
ha-manager status

# Listar todos los CTs del nodo
pct list

# Arrancar / parar / reiniciar un CT
pct start <CTID>
pct stop <CTID>
pct restart <CTID>

# Entrar a la consola de un CT
pct enter <CTID>

# Ver configuración de un CT
cat /etc/pve/lxc/<CTID>.conf

# Redimensionar disco de un CT
pct resize <CTID> rootfs <TAMAÑOg>

# Estado de servicios Proxmox
systemctl list-units 'pve*' 'corosync*'

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
| `https://192.168.1.11:8006` | Nodo srv-01 (vista del mismo clúster) |
| `https://192.168.1.XX:8006` | Interfaz web de este nodo |

> Ambas URLs muestran la vista completa del clúster. Accesible solo desde la LAN.

---

## 15. Lo que falta documentar / configurar

### Pendiente de completar en este documento
- **IP del nodo** — no visible en el historial; marcar en la sección de red y en la tabla del clúster
- **Interfaz de red física** — verificar con `ip link show` (`enp1s0` u otro)
- **Inventario de CTs** — solo se conoce el CT 198; completar tabla con todos los que corren en este nodo
- **Nombre y función del CT 198** — conocido por el `pct resize` pero sin más detalle

### Pendiente de configurar (igual que srv-01)
- **Backups automáticos** — sin schedule configurado; riesgo de pérdida ante fallo de disco
- **SMART monitoring** — sin vigilancia del estado físico de los discos (`smartmontools`)
- **Alertas Grafana** — sin notificaciones si un CT o el nodo cae
- **Firewall Proxmox** — seguridad solo a nivel de UFW por CT, sin firewall en el host
- **Actualizaciones automáticas** — el host no se actualiza solo (`unattended-upgrades`)