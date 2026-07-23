# CI VPN: WireGuard

El contenedor de **VPN (WireGuard)** es la pieza que une tu red local con el mundo exterior de forma segura. En la Raspberry Pi 5, WireGuard ofrece un rendimiento cercano a la velocidad de cable con un uso de CPU mínimo.

---

## 1. Configuración del Host (Raspberry Pi 5)

Antes de tocar el contenedor, el Host debe estar preparado:

```bash
sudo apt update && sudo apt install -y wireguard-tools
sudo modprobe wireguard
# Verificar que el módulo cargó
lsmod | grep wireguard
```

---

## 2. Despliegue del Contenedor

Desde el host, clonamos la base y aplicamos los permisos especiales de kernel:


```bash
sudo lxc-copy -n B0-deb12 -N CI04-vpn
```

### Editar Configuración del LXC

`sudo nano /var/lib/lxc/CI04-vpn/config`
Copia el contenido de config.conf

### Iniciar y configurar DNS

```bash
sudo lxc-start -n CI04-vpn
sudo lxc-attach -n CI04-vpn

# Forzar DNS de nuestro Pi-hole
rm /etc/resolv.conf
echo "nameserver 192.168.1.101" > /etc/resolv.conf
echo "nameserver 8.8.8.8" >> /etc/resolv.conf
```

---

## 3. Instalación y Configuración Manual
Dentro del contenedor, instalamos las herramientas necesarias:

```bash
apt update && apt install -y wireguard wireguard-tools qrencode nftables
```

### Generación de llaves
```bash
cd /etc/wireguard
umask 077
# Llaves del servidor
wg genkey | tee private.key | wg pubkey > public.key
# Llaves del cliente (Móvil)
wg genkey | tee client_private.key | wg pubkey > client_public.key
```

### Archivo de Configuración `wg0.conf`
`nano /etc/wireguard/wg0.conf`

```ini
[Interface]
Address = 10.0.1.1/24
ListenPort = 51820
PrivateKey = <CONTENIDO_DE_private.key>

[Peer]
PublicKey = <CONTENIDO_DE_client_public.key>
AllowedIPs = 10.0.1.2/32
```

---

## 4. Configuración de Red (Forwarding y NAT)
Para que el tráfico fluya desde la VPN a Internet:

```bash
# Agregar ruta a 10.0.1.0/24
sudo nmcli connection modify br0 +ipv4.routes "10.0.1.0/24 0.0.0.0"
$ sudo nmcli connection up br0

# Habilitar IP Forwarding
echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
sysctl -p

# Configurar NAT con nftables
nano /etc/nftables.conf
```

**Copia el contenido de `nftables.conf`:**

```
**Aplicar y activar:**
```bash
nft -f /etc/nftables.conf
systemctl enable nftables
systemctl enable wg-quick@wg0
systemctl start wg-quick@wg0
```

---

## 5. Generación del Cliente (Código QR)
Crea el perfil para tu smartphone:
`nano cliente.conf`

```ini
[Interface]
PrivateKey = <CONTENIDO_DE_client_private.key>
Address = 10.0.1.2/24
DNS = 192.168.1.101

[Peer]
PublicKey = <CONTENIDO_DE_public.key_SERVIDOR>
Endpoint = vpn.davidalvarezp.com:51820
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 20
```

**Mostrar QR:** `qrencode -t ansiutf8 < cliente.conf`



---

## Resumen de Infraestructura Terminada

| Servicio | IP | Función |
| :--- | :--- | :--- |
| **Pi-hole** | .101 | DNS y AdBlock local/remoto |
| **Proxy** | .102 | Nginx Reverse Proxy |
| **Stats** | .103 | Grafana & Prometheus |
| **VPN** | .104 | Acceso remoto seguro (WireGuard) |

