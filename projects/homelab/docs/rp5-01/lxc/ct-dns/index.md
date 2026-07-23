# ct-dns: Pi-Hole

El primer contenedor que creo es el DNS (Domain Name System), porque sin DNS las cosas **no** funcionan.

## 1. Despliegue del Contenedor

En el host, clonamos el contenedor base:

```bash
sudo lxc-copy -n ct-13 -N ct-dns
```

## 2. Configuración de Red (IP Estática)

Modificamos el fichero configuración `/var/lib/lxc/ct-dns/config` con el contenido del archivo [config](config.md).

```bash
sudo lxc-start -n ct-dns
sudo lxc-attach -n ct-dns
```

Editamos `nano /etc/systemd/network/eth0.network`

```conf
[Match]
Name=eth0

[Network]
Address=10.0.10.100/24
Gateway=10.0.10.1
DNS=1.1.1.1
DNS=8.8.8.8
```


Para poder instalar y resolver dominios, congiguramos DNS:

```bash
rm /etc/resolv.conf
echo "nameserver 8.8.8.8" > /etc/resolv.conf
echo "nameserver 1.1.1.1" >> /etc/resolv.conf
```

## 3. Instalación de Pi-hole

Ejecutaremos el script oficial de instalación de [Pi-hole](https://pi-hole.net/).

```bash
curl -sSL https://install.pi-hole.net | bash
```

**En el asistente seleccionaremos**:
* **Interface:** `eth0`.
* **Upstream DNS:** Google o Cloudflare.
* **Web Interface:** On.
* **Log Queries:** On (para Grafana).

## 4. Ajustes de Seguridad

### Firewall

Pi-hole necesita abrir varios puertos para funcionar como DNS y para su panel web.

```bash
# DNS (Tráfico de red)
ufw allow 53/tcp
ufw allow 53/udp

# Panel Web (Administración)
ufw allow 80/tcp
ufw allow 443/tcp

# Opcional, si quieres que pi-hole actúe como servidor DHCP
ufw allow 67/udp
ufw allow 68/udp

# Recargar reglas
ufw reload
```

### Acceso Web

Ahora ya podemos acceder a la interfaz web entrando en http o https :$IP/admin

La contraseña se establece ejecutando:

```bash
pihole setpassword
```

## 5. Monitorización

Como ya instalamos el **Node Exporter** en el contenedor base, Pi-hole ya envía las métricas a Grafana automáticamente.


## 6. Bonus: Evitar conflictos con el puerto 53
En algunas instalaciones de Debian, `systemd-resolved` utiliza el puerto 53. Si el instalador de Pi-hole da error, ejecuta esto:
```bash
systemctl stop systemd-resolved
systemctl disable systemd-resolved
```
