# CT rp5-01-ct-dns: DNS + Bloqueador de Anuncios

Contenedor dedicado a resolver el DNS de toda la red local mediante **Pi-hole**, actuando como servidor DNS primario del homelab. Bloquea anuncios y rastreadores a nivel de red, y expone métricas al stack de monitorización mediante **Prometheus Node Exporter**.

---

## 1. Despliegue del Contenedor

En el nodo **Raspberry Pi 5** (`rp5-01`), creamos el contenedor Debian 12:

- **CPU** 2 sockets
- **RAM** 512 MB
- **Disco** 4 GB
- **Red** 192.168.1.20

---

## 2. Preparación del Sistema

```bash
# Actualización base y utilidades
apt update && apt install -y bash-completion curl
echo "source /etc/bash_completion" >> ~/.bashrc
source ~/.bashrc

# IP estática via systemd-networkd
mkdir -p /etc/systemd/network
cat > /etc/systemd/network/eth0.network << 'EOF'
[Match]
Name=eth0

[Network]
DHCP=no
Address=192.168.1.20/24
Gateway=192.168.1.1
DNS=8.8.8.8
EOF

systemctl enable systemd-networkd
systemctl restart systemd-networkd

# Verificar conectividad
ping -c 2 8.8.8.8
```

---

## 3. Instalación de Pi-hole

```bash
# Instalación desatendida (el script es interactivo la primera vez)
curl -sSL https://install.pi-hole.net | bash

# Establecer contraseña del panel de administración
pihole setpassword
```

> Durante la instalación seleccionar:
> - **Interfaz**: `eth0`
> - **DNS upstream**: Cloudflare (`1.1.1.1`) o Google (`8.8.8.8`)
> - **Instalación del servidor web**: Sí (lighttpd)
> - **Logging**: Sí

---

## 4. Estructura de Ficheros

```
/etc/pihole/
├── pihole.toml              ← Configuración principal de Pi-hole v6
├── gravity.db               ← Base de datos de listas de bloqueo
└── custom.list              ← Registros DNS locales personalizados

/etc/systemd/network/
└── eth0.network             ← Configuración de red estática

/etc/cron.weekly/
└── pihole-update            ← Actualización semanal automática de listas
```

---

## 5. Servicios y Cuentas

| Servicio | Puerto | Descripción |
|---|---|---|
| **pihole-FTL** | 53 UDP/TCP | Servidor DNS |
| **lighttpd** | 80 TCP | Panel de administración web |
| **prometheus-node-exporter** | 9100 TCP | Métricas del sistema para Grafana |
| **Panel admin** | http://dns.dap.gal/admin | Acceso via Traefik (LAN) |

---

## 6. Flujo DNS

```
Dispositivos de la red (192.168.1.0/24)
              │
              │ DNS query → 192.168.1.20:53
              ▼
       Pi-hole (rp5-01-ct-dns)
              │
     ┌────────┴────────┐
     │                 │
  Bloqueado        Permitido
  (NXDOMAIN)           │
                        │ reenvío upstream
                        ▼
              1.1.1.1 / 8.8.8.8
```

```
LAN → dns.dap.gal
              │
              ▼
      Traefik (:80, lan)
              │
              │ redirect /admin/
              ▼
  http://192.168.1.20/admin    ← Panel Pi-hole
```

---

## 7. Configuración del Router

Para que Pi-hole sea el DNS de toda la red, configurar en el router:

| Parámetro | Valor |
|---|---|
| **DNS primario** | 192.168.1.20 |
| **DNS secundario** | 1.1.1.1 *(fallback si Pi-hole cae)* |

> También puede configurarse por dispositivo o por VLAN si el router lo permite.

---

## 8. Registros DNS Locales

Pi-hole puede resolver nombres internos sin depender de Traefik para el tráfico LAN.  
Añadir en **Panel admin → Local DNS → DNS Records**:

| Dominio | IP |
|---|---|
| `dns.dap.gal` | 192.168.1.20 |
| `proxy.dap.gal` | 192.168.1.31 |
| `stats.dap.gal` | 192.168.1.32 |
| `home.dap.gal` | 192.168.1.33 |

---

## 9. Actualizaciones Automáticas

```bash
# Actualización semanal de listas de bloqueo (gravity)
cat > /etc/cron.weekly/pihole-update << 'EOF'
#!/bin/bash
pihole -up
EOF
chmod +x /etc/cron.weekly/pihole-update

# Actualizaciones de seguridad del sistema operativo
apt install -y unattended-upgrades
dpkg-reconfigure -f noninteractive unattended-upgrades
```

---

## 10. Monitorización

### Node Exporter (métricas del sistema)

```bash
# Ya instalado
apt install -y prometheus-node-exporter
systemctl enable prometheus-node-exporter
systemctl start prometheus-node-exporter
```

Expone métricas en `http://192.168.1.20:9100/metrics`.  
Prometheus recoge estas métricas automáticamente y Grafana las visualiza en el dashboard del homelab.

### Pi-hole Exporter (métricas DNS)

Para exponer estadísticas de Pi-hole (queries bloqueadas, dominios, clientes) en Grafana:

```bash
# Descargar pihole-exporter
curl -L https://github.com/eko/pihole-exporter/releases/latest/download/pihole_exporter-linux-arm64 \
    -o /usr/local/bin/pihole-exporter
chmod +x /usr/local/bin/pihole-exporter

# Servicio systemd
cat > /etc/systemd/system/pihole-exporter.service << 'EOF'
[Unit]
Description=Pi-hole Prometheus Exporter
After=network.target

[Service]
ExecStart=/usr/local/bin/pihole-exporter \
    -pihole_hostname 192.168.1.20 \
    -pihole_port 80
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now pihole-exporter
```

Expone métricas en `http://192.168.1.20:9617/metrics`.

> Dashboard recomendado para Grafana: **ID 10176** (Pi-hole Exporter).

---

## 11. Comandos Útiles

```bash
# Estado de Pi-hole
pihole status

# Estadísticas rápidas por consola
pihole -c

# Actualizar listas de bloqueo manualmente
pihole -g

# Actualizar Pi-hole
pihole -up

# Activar / desactivar Pi-hole temporalmente
pihole disable 5m     # desactiva 5 minutos
pihole enable

# Consultar si un dominio está bloqueado
pihole -q ads.example.com

# Ver logs DNS en tiempo real
pihole -t

# Estado de los servicios
systemctl status pihole-FTL
systemctl status lighttpd
systemctl status prometheus-node-exporter

# Comprobar que el puerto 53 está escuchando
ss -ulnp | grep :53
ss -tlnp | grep :53
```

---

## 12. Logs

```bash
# Log de consultas DNS (últimas 20 líneas)
tail -20 /var/log/pihole/pihole.log

# Log de FTL
tail -20 /var/log/pihole/FTL.log

# Desde el panel web
# Admin → Query Log  →  filtro por dominio / cliente / estado
```