# CT rp5-01-ct-vpn: VPN WireGuard

Contenedor dedicado a proporcionar acceso remoto seguro a la red del homelab mediante **WireGuard**. Permite conectarse desde el portátil, el móvil o cualquier otro dispositivo como si estuvieras en casa, con acceso completo a todos los servicios internos y con DNS resuelto por Pi-hole.

---

## 1. Arquitectura

```
Dispositivo externo (laptop / móvil)
          │
          │ WireGuard UDP → <IP-pública>:51820
          ▼
Router doméstico (NAT/port forward → 192.168.1.22:51820)
          │
          ▼
CT rp5-01-ct-vpn — WireGuard server (192.168.1.22)
          │
          │ Túnel: 10.8.0.0/24
          │
          ├── Acceso a toda la LAN (192.168.1.0/24)
          └── DNS → Pi-hole (192.168.1.20)
```

| Red | Rango | Uso |
|---|---|---|
| LAN homelab | 192.168.1.0/24 | Red local |
| VPN WireGuard | 10.8.0.0/24 | Túnel entre cliente y servidor |
| Servidor VPN | 10.8.0.1 | IP del servidor dentro del túnel |
| Clientes | 10.8.0.2 — 10.8.0.254 | IPs asignadas a cada dispositivo |

---

## 2. Despliegue del Contenedor en Proxmox

### Crear el CT

En la UI de Proxmox (`rp5-01`), crear un contenedor Debian 12 ARM64 con:

- **CPU** 1 socket
- **RAM** 256 MB
- **Disco** 2 GB
- **Red** 192.168.1.22

### Configuración especial del CT (obligatoria para WireGuard)

WireGuard necesita acceso al módulo de red del kernel del host. Editar la configuración del CT desde `rp5-01`:

```bash
# En el HOST rp5-01 (no en el CT)
nano /etc/pve/lxc/<CTID>.conf
```

Añadir al final:

```
lxc.cgroup2.devices.allow: c 10:200 rwm
lxc.mount.entry: /dev/net/tun dev/net/tun none bind,create=file 0 0
features: nesting=1
```

Verificar que el módulo WireGuard está cargado en el host:

```bash
# En el HOST rp5-01
modprobe wireguard
echo "wireguard" >> /etc/modules
lsmod | grep wireguard
```

---

## 3. Preparación del Sistema (dentro del CT)

```bash
# Actualización base
apt update && apt upgrade -y
apt install -y wireguard wireguard-tools curl iptables

# Habilitar reenvío de paquetes IP (necesario para enrutar tráfico LAN)
echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
sysctl -p

# Verificar
sysctl net.ipv4.ip_forward
# Debe devolver: net.ipv4.ip_forward = 1
```

---

## 4. Estructura de Ficheros

```
/etc/wireguard/
├── wg0.conf             ← Configuración del servidor WireGuard
├── server_private.key   ← Clave privada del servidor (chmod 600)
├── server_public.key    ← Clave pública del servidor
└── clientes/            ← Configuraciones de cada cliente
    ├── laptop.conf
    └── movil.conf
```

---

## 5. Generación de Claves

```bash
mkdir -p /etc/wireguard/clientes
cd /etc/wireguard

# Par de claves del SERVIDOR
wg genkey | tee server_private.key | wg pubkey > server_public.key
chmod 600 server_private.key

# Par de claves del cliente: LAPTOP
wg genkey | tee clientes/laptop_private.key | wg pubkey > clientes/laptop_public.key

# Par de claves del cliente: MÓVIL
wg genkey | tee clientes/movil_private.key | wg pubkey > clientes/movil_public.key

# Ver las claves generadas
echo "=== SERVIDOR ===" && cat server_public.key
echo "=== LAPTOP ===" && cat clientes/laptop_public.key
echo "=== MÓVIL ===" && cat clientes/movil_public.key
```

---

## 6. Configuración del Servidor

### `/etc/wireguard/wg0.conf`

```ini
[Interface]
Address    = 10.8.0.1/24
ListenPort = 51820
PrivateKey = <contenido de server_private.key>

# Enrutar tráfico de clientes hacia la LAN
# IMPORTANTE: cada PostUp/PostDown debe ir en una sola línea — WireGuard no soporta \ para continuar línea
PostUp   = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -A FORWARD -o wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -D FORWARD -o wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

# ── LAPTOP ───────────────────────────────────────────────────
[Peer]
PublicKey  = <contenido de clientes/laptop_public.key>
AllowedIPs = 10.8.0.2/32

# ── MÓVIL ────────────────────────────────────────────────────
[Peer]
PublicKey  = <contenido de clientes/movil_public.key>
AllowedIPs = 10.8.0.3/32
```

```bash
chmod 600 /etc/wireguard/wg0.conf

# Habilitar inicio automático y arrancar
systemctl enable wg-quick@wg0
systemctl start wg-quick@wg0

# Verificar estado (el estado normal es "active (exited)", no "running")
systemctl status wg-quick@wg0
wg show

# IMPORTANTE: no usar wg-quick up/down directamente una vez gestionado por systemd
# Si se levanta manualmente primero, bajar antes de que systemd lo arranque:
#   wg-quick down wg0 && systemctl start wg-quick@wg0
# En adelante usar siempre: systemctl start/stop/restart wg-quick@wg0
```

---

## 7. Configuración de Clientes

### Laptop — `/etc/wireguard/clientes/laptop.conf`

```ini
[Interface]
PrivateKey = <contenido de clientes/laptop_private.key>
Address    = 10.8.0.2/32
DNS        = 192.168.1.20        # Pi-hole del homelab

[Peer]
PublicKey  = <contenido de server_public.key>
Endpoint   = <IP-PÚBLICA-O-DDNS>:51820
AllowedIPs = 0.0.0.0/0           # Todo el tráfico por el túnel (full tunnel)
             # Alternativa para solo acceder a la LAN (split tunnel):
             # AllowedIPs = 192.168.1.0/24, 10.8.0.0/24
PersistentKeepalive = 25
```

### Móvil — `/etc/wireguard/clientes/movil.conf`

```ini
[Interface]
PrivateKey = <contenido de clientes/movil_private.key>
Address    = 10.8.0.3/32
DNS        = 192.168.1.20

[Peer]
PublicKey  = <contenido de server_public.key>
Endpoint   = <IP-PÚBLICA-O-DDNS>:51820
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
```

### Generar QR para el móvil

```bash
apt install -y qrencode

# Muestra el QR directamente en la terminal
qrencode -t ansiutf8 < /etc/wireguard/clientes/movil.conf
```

> Escanear con la app **WireGuard** (iOS / Android).

---

## 8. Instalar WireGuard en el Laptop (Linux)

```bash
# En el laptop (Debian/Ubuntu)
apt install -y wireguard

# Copiar el fichero de configuración
scp root@192.168.1.22:/etc/wireguard/clientes/laptop.conf \
    /etc/wireguard/wg0.conf

chmod 600 /etc/wireguard/wg0.conf

# Conectar
wg-quick up wg0

# Desconectar
wg-quick down wg0

# Conexión automática al arranque (opcional)
systemctl enable wg-quick@wg0
```

---

## 9. Router — Port Forwarding

En la interfaz del router, crear una regla de reenvío de puertos:

| Campo | Valor |
|---|---|
| **Protocolo** | UDP |
| **Puerto externo** | 51820 |
| **IP destino** | 192.168.1.22 |
| **Puerto destino** | 51820 |

> Si tienes IP pública dinámica, configurar un cliente DDNS en el router (DuckDNS, No-IP, etc.) y usar ese hostname como `Endpoint` en los ficheros de cliente.

---

## 10. Cortafuegos (UFW)

```bash
ufw default deny incoming
ufw default deny outgoing

# WireGuard (entrada desde internet)
ufw allow in 51820/udp

# DNS hacia Pi-hole
ufw allow out to 192.168.1.20 port 53 proto udp
ufw allow out to 192.168.1.20 port 53 proto tcp

# NTP
ufw allow out 123/udp

# Tráfico de clientes VPN hacia la LAN
ufw allow out to 192.168.1.0/24

# SSH administrativo desde la LAN
ufw allow in from 192.168.1.0/24 to any port 22 proto tcp

# Node Exporter (desde Prometheus)
ufw allow in from 192.168.1.32 to any port 9100 proto tcp

ufw --force enable
ufw status verbose
```

---

## 11. Monitorización

```bash
apt install -y prometheus-node-exporter
systemctl enable prometheus-node-exporter
systemctl start prometheus-node-exporter
```

Expone métricas en `http://192.168.1.22:9100/metrics`.

---

## 12. Añadir un Nuevo Cliente

```bash
# 1. Generar claves
cd /etc/wireguard
wg genkey | tee clientes/nuevo_private.key | wg pubkey > clientes/nuevo_public.key

# 2. Añadir el peer al servidor (sin reiniciar el servicio)
wg set wg0 peer <nuevo_public_key> allowed-ips 10.8.0.X/32

# 3. Guardar el cambio en wg0.conf
wg-quick save wg0

# 4. Crear el fichero de configuración del cliente
cat > /etc/wireguard/clientes/nuevo.conf << EOF
[Interface]
PrivateKey = <nuevo_private_key>
Address    = 10.8.0.X/32
DNS        = 192.168.1.20

[Peer]
PublicKey  = $(cat server_public.key)
Endpoint   = <IP-PÚBLICA>:51820
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
EOF

# 5. Generar QR si es móvil
qrencode -t ansiutf8 < /etc/wireguard/clientes/nuevo.conf
```

---

## 13. Comandos Útiles

```bash
# Estado del túnel y peers conectados
wg show

# Ver tráfico por peer
wg show wg0 transfer

# Ver último handshake de cada cliente (si está conectado)
wg show wg0 latest-handshakes

# Reiniciar WireGuard
systemctl restart wg-quick@wg0

# Subir / bajar el túnel manualmente
wg-quick up wg0
wg-quick down wg0

# Ver logs
journalctl -u wg-quick@wg0 -f

# Verificar enrutamiento
ip route show table main
iptables -t nat -L -n -v

# Test de conectividad desde un cliente conectado
ping 192.168.1.1        # router
ping 192.168.1.20       # Pi-hole
curl http://192.168.1.31:8888/api/overview   # Traefik dashboard
```

---

## 14. Tabla de Clientes

| Cliente | IP VPN | Clave pública | Descripción |
|---|---|---|---|
| Servidor | 10.8.0.1 | *(server_public.key)* | CT rp5-01-ct-vpn |
| Laptop | 10.8.0.2 | *(laptop_public.key)* | Portátil principal |
| Móvil | 10.8.0.3 | *(movil_public.key)* | Teléfono |
| *(añadir)* | 10.8.0.4 | — | — |