# CI Proxy: Nginx Reverse Proxy

En segundo lugar creé el contenedor proxy (Nginx Reverse Proxy), para extablecer que dirección IP va asociada a cada dominio.


## Arquitectura de Red

### 1. Capa de Gestión (Subdominios)
Acceso directo a las herramientas de administración.
* **DNS:** `dns.dap.gal` (Pi-hole)
* **Proxy:** `proxy.dap.gal` (Traefik Dashboard)
* **Métricas:** `stats.dap.gal` (Grafana)
* **VPN:** `vpn.dap.gal` (WireGuard Web UI)
* **Dashboard:** `home.dap.gal` (Homepage)

### 2. Capa Pública (Path-based)
Servicios expuestos al exterior.
* **Landing Page:** `dap.gal/`
* **Blog:** `dap.gal/blog` (Ghost)


## 1. Despliegue del Contenedor

Desde el host:

```bash
sudo lxc-copy -n CB01-deb12 -N CI02-PROXY

# Editar config
sudo nano /var/lib/lxc/CI02-PROXY/config 

# Iniciar
sudo lxc-start -n CI02-PROXY
sudo lxc-attach -n CI02-PROXY

# Configuramos DNS
rm /etc/resolv.conf
echo "nameserver 192.168.1.11" > /etc/resolv.conf
echo "nameserver 8.8.8.8" >> /etc/resolv.conf

```

## 2. Instalación y Configuración de Traefik

### 1. Preparación del Sistema
Actualizamos repositorios e instalamos las dependencias básicas necesarias.

```bash
apt update && apt upgrade -y
apt install -y curl wget debian-archive-keyring lsb-release gnupg2
```

### 2. Instalación de Traefik
Descargamos el binario oficial (método recomendado para LXC para evitar sobrecarga de Docker).

```bash
# Obtener la última versión de la página de lanzamientos de GitHub
wget https://github.com/traefik/traefik/releases/download/v3.0.0/traefik_v3.0.0_linux_arm64.tar.gz # Ajusta si es amd64
tar -zxvf traefik_v3.0.0_linux_arm64.tar.gz
mv traefik /usr/local/bin/
chmod +x /usr/local/bin/traefik
```

## 3. Estructura de Directorios y Permisos
Creamos el entorno de configuración profesional.

```bash
mkdir -p /etc/traefik/conf.d
mkdir -p /etc/traefik/acme
touch /etc/traefik/traefik.yml
touch /etc/traefik/acme/acme.json
chmod 600 /etc/traefik/acme/acme.json # Requisito de seguridad para SSL
```

## 4. Configuración Estática (`traefik.yml`)
Este archivo define los **EntryPoints** (puertos) y el **Certificate Resolver** para Cloudflare.

`nano /etc/traefik/traefik.yml`

```yaml
api:
  dashboard: true
  insecure: false

entryPoints:
  web:
    address: ":80"
    http:
      redirections:
        entryPoint:
          to: websecure
          scheme: https
  websecure:
    address: ":443"

providers:
  file:
    directory: /etc/traefik/conf.d
    watch: true

certificatesResolvers:
  cloudflare:
    acme:
      email: tu-email@ejemplo.com
      storage: /etc/traefik/acme/acme.json
      dnsChallenge:
        provider: cloudflare
        resolvers:
          - "1.1.1.1:53"
          - "8.8.8.8:53"
```

## 5. Configuración Dinámica (`conf.d/rules.yml`)
Aquí es donde ocurre la magia del enrutado que definimos.

`nano /etc/traefik/conf.d/rules.yml`

Copiar el contenido de [rules](rules.md)

## 6. Variables de Entorno (Cloudflare API)
Traefik necesita tu Token de Cloudflare para validar el DNS Challenge. Lo configuramos en el servicio de Systemd.

`nano /etc/systemd/system/traefik.service`

```ini
[Unit]
Description=Traefik
After=network-online.target

[Service]
Type=simple
User=root
Group=root
Environment=CF_DNS_API_TOKEN=TU_TOKEN_DE_CLOUDFLARE_AQUI
ExecStart=/usr/local/bin/traefik --configFile=/etc/traefik/traefik.yml
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

## 7. Lanzamiento y Verificación
Habilitamos el servicio y comprobamos que todo esté en orden.

```bash
systemctl daemon-reload
systemctl enable traefik
systemctl start traefik

# Ver logs en tiempo real por si falla algo
journalctl -u traefik -f
```

---

1. Configuración de Reglas Básicas
Bash
# 1. Denegar todo el tráfico entrante por defecto (Seguridad)
ufw default deny incoming

# 2. Permitir todo el tráfico saliente (Para que Traefik llegue a los otros LXC)
ufw default allow outgoing

# 3. Permitir SSH (¡IMPORTANTE! Si no, te echarás a ti mismo del contenedor)
ufw allow ssh

# 4. Puertos Web Estándar (Entrada desde el exterior)
ufw allow 80/tcp
ufw allow 443/tcp

# 5. Puerto del Dashboard de Traefik (Uso interno)
# Aunque lo sacamos por proxy.dap.gal (443), el binario escucha internamente aquí
ufw allow 8080/tcp

---

## 6. Integración con Monitoreo
Como ya tienes el **Node Exporter** en la base, Grafana ya verá la CPU.
