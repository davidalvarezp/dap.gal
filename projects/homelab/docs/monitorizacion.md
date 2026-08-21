# Prometheus Exporters - Chuleta de instalación

Instalación rápida de todos los exportadores para un homelab con Proxmox.

---

# 🌍 En TODOS los Linux (Proxmox, VMs y LXC)

## Node Exporter ⭐⭐⭐⭐⭐

**Exporta:**

- CPU
- RAM
- Swap
- Disco
- Filesystems
- Red
- Procesos
- Uptime
- Load Average

**Instalación**

```bash
apt update
apt install -y prometheus-node-exporter
```

Puerto:

```
9100
```

---

# 🖥️ Solo Hosts Proxmox

## SMART (smartmontools)

**Exporta:**

- Salud del disco
- Temperatura
- Vida útil SSD
- Sectores reasignados
- Horas de funcionamiento
- SMART Health

**Instalación**

```bash
apt install -y smartmontools
```

Comprobar:

```bash
smartctl -a /dev/sda
```

---

## lm-sensors

**Exporta:**

- Temperaturas CPU
- Temperaturas placa
- Ventiladores
- Voltajes

**Instalación**

```bash
apt install -y lm-sensors
```

Detectar sensores:

```bash
sensors-detect
```

Ver sensores:

```bash
sensors
```

---

## nvme-cli

**Exporta**

- Estado NVMe
- Temperatura
- Wear Level
- SMART NVMe

**Instalación**

```bash
apt install -y nvme-cli
```

Comprobar:

```bash
nvme smart-log /dev/nvme0
```

---

## mdadm (solo RAID software)

**Exporta**

- Estado RAID
- Discos degradados
- Reconstrucciones

**Instalación**

```bash
apt install -y mdadm
```

---

## MegaCLI / StorCLI (solo MegaRAID)

**Exporta**

- Estado RAID
- Estado discos
- BBU
- Caché

(No disponible mediante apt en Debian)

---

# 📦 Solo contenedores LXC

## Node Exporter

```bash
apt install -y prometheus-node-exporter
```

No instalar nada más.

---

# 💻 Solo Máquinas Virtuales

## Node Exporter

```bash
apt install -y prometheus-node-exporter
```

---

# ☁️ Solo una máquina (Servidor Prometheus)

## Prometheus

**Exporta**

Recoge todas las métricas.

```bash
apt install -y prometheus
```

Puerto

```
9090
```

---

## Grafana

**Visualiza**

- Dashboards
- Alertas
- Gráficas

```bash
apt install -y grafana
```

Puerto

```
3000
```

---

## Alertmanager

**Gestiona**

- Alertas
- Telegram
- Discord
- Email
- Slack
- Webhook

```bash
apt install -y prometheus-alertmanager
```

Puerto

```
9093
```

---

## Blackbox Exporter

**Exporta**

- Ping
- HTTP
- HTTPS
- TCP
- DNS
- ICMP

```bash
apt install -y prometheus-blackbox-exporter
```

Puerto

```
9115
```

---

## SNMP Exporter

**Exporta**

- Switches
- Routers
- APs
- NAS
- UPS
- Impresoras

```bash
apt install -y prometheus-snmp-exporter
```

Puerto

```
9116
```

---

# 🔧 Proxmox

## Proxmox VE Exporter

**Exporta**

- Cluster
- VMs
- LXC
- CPU
- RAM
- HA
- Backups
- Replicación
- Almacenamiento

No existe un paquete oficial en Debian.

Se instala normalmente mediante Docker o Python.

---

## ZFS Exporter

**Exporta**

- ARC
- L2ARC
- ZIL
- Pools
- Scrub
- Errores
- Dataset usage

No existe paquete oficial en Debian.

Normalmente se instala desde GitHub o Docker.

---

## IPMI Exporter

**Exporta**

- Temperaturas
- Ventiladores
- Consumo
- PSU
- Sensores

No existe paquete oficial en Debian.

Normalmente se instala mediante Docker.

---

# ✅ Resumen

| Instalar | Hosts | Disponible por APT |
|----------|------|--------------------|
| prometheus-node-exporter | Todos | ✅ |
| smartmontools | Proxmox | ✅ |
| lm-sensors | Proxmox | ✅ |
| nvme-cli | Proxmox | ✅ |
| mdadm | Solo RAID software | ✅ |
| prometheus | Servidor | ✅ |
| grafana | Servidor | ✅ |
| prometheus-alertmanager | Servidor | ✅ |
| prometheus-blackbox-exporter | Servidor | ✅ |
| prometheus-snmp-exporter | Servidor | ✅ |
| proxmoxve-exporter | Servidor | ❌ |
| zfs-exporter | Hosts ZFS | ❌ |
| ipmi-exporter | Hosts con BMC | ❌ |