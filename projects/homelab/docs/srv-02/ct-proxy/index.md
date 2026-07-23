# CT srv-01-ct-proxy: Reverse Proxy

Contenedor dedicado a enrutar el tráfico entrante (internet y LAN) hacia los servicios internos del homelab mediante **Traefik v3.3.4**, con soporte para certificados SSL automáticos vía **Let's Encrypt + Cloudflare DNS**.

---

## 1. Despliegue del Contenedor

En el nodo Proxmox del M920x, creamos el contenedor Debian 12:

- **CPU** 1 socket
- **RAM** 512 MB
- **Disco** 8 GB
- **Red** 192.168.1.31

---

## 2. Preparación del Sistema

```bash
# Actualización base
apt update && apt upgrade -y && apt install -y curl wget jq

# Descargar e instalar Traefik v3.3.4
wget -q https://github.com/traefik/traefik/releases/download/v3.3.4/traefik_v3.3.4_linux_amd64.tar.gz \
    -O /tmp/traefik.tar.gz
tar -xzf /tmp/traefik.tar.gz -C /tmp
install -m 755 /tmp/traefik /usr/local/bin/traefik
rm -f /tmp/traefik.tar.gz /tmp/traefik

# Verificar instalación
traefik version

# Usuario de sistema sin shell
useradd -r -s /usr/sbin/nologin traefik

# Directorios de configuración y logs
mkdir -p /etc/traefik/conf.d
mkdir -p /etc/traefik/env
mkdir -p /var/log/traefik
chown -R traefik:traefik /etc/traefik /var/log/traefik

# Permiso para abrir puertos bajos (80) sin root
setcap 'cap_net_bind_service=+ep' /usr/local/bin/traefik

# Fichero ACME para certificados SSL
touch /etc/traefik/acme.json
chmod 600 /etc/traefik/acme.json
```

---

## 3. Estructura de Ficheros

```
/etc/traefik/
├── traefik.yml              ← Configuración principal
├── acme.json                ← Almacén de certificados Let's Encrypt (chmod 600)
├── conf.d/
│   └── dap.gal.yml          ← Rutas HTTP (internet + LAN)
└── env/
    └── cloudflare.env       ← Token API de Cloudflare (chmod 600)

/var/log/traefik/
├── traefik.log              ← Log del servicio
└── access.log               ← Log de accesos HTTP
```

---

## 4. Servicios y Cuentas

| Servicio | Detalle | Descripción |
|---|---|---|
| **Traefik** | v3.3.4 | Reverse proxy y gestor de rutas |
| **Dashboard** | http://proxy.dap.gal | Panel de control de Traefik |
| **Let's Encrypt** | ACME via DNS | Certificados SSL automáticos |
| **Cloudflare** | DNS Challenge | Proveedor DNS para validación ACME |
| **Dominio público** | dap.gal | Dominio principal del homelab |

---

## 5. Flujo de Enrutamiento

```
Internet
    │
    │ :8080 (entrypoint: web)
    ▼
Traefik (192.168.1.31)
    │
    ├── dap.gal / www.dap.gal ──────→ CT Hosting (192.168.1.40:80)
    │
    │ :80 (entrypoint: lan)
    ▼
Traefik (solo red local)
    │
    ├── dns.dap.gal   ──────────────→ Pi-hole    (192.168.1.20:80)
    ├── proxy.dap.gal ──────────────→ Dashboard  (192.168.1.31:8888)
    ├── stats.dap.gal ──────────────→ Grafana    (192.168.1.32:3000)
    └── home.dap.gal  ──────────────→ Homepage   (192.168.1.33:80)
```

> El router/NAT reenvía el puerto 8080 externo a `192.168.1.31:8080`.  
> El tráfico LAN entra directamente por el puerto 80.

---

## 6. Configuración Principal

### `/etc/traefik/traefik.yml`

```yaml
log:
  level: INFO
  filePath: /var/log/traefik/traefik.log

accessLog:
  filePath: /var/log/traefik/access.log

api:
  dashboard: true
  insecure: true

entryPoints:
  web:
    address: ":8080"
    forwardedHeaders:
      trustedIPs:
        - "192.168.1.39"
  websecure:
    address: ":443"
    forwardedHeaders:
      trustedIPs:
        - "192.168.1.0/24"
  lan:
    address: ":80"
    forwardedHeaders:
      trustedIPs:
        - "192.168.1.0/24"
    http:
      redirections:
        entryPoint:
          to: websecure
          scheme: https
  ssh:
    address: ":2222"
  traefik:
    address: ":8888"

certificatesResolvers:
  cloudflare:
    acme:
      email: mail@dap.gal
      storage: /etc/traefik/acme.json
      dnsChallenge:
        provider: cloudflare
        resolvers:
          - "1.1.1.1:53"

providers:
  file:
    directory: /etc/traefik/conf.d
    watch: true
```

### `/etc/traefik/env/cloudflare.env`

```env
CF_DNS_API_TOKEN=tu_token_api_cloudflare
```

> Permisos: `chmod 600 /etc/traefik/env/cloudflare.env`

---

## 7. Rutas HTTP

### `/etc/traefik/conf.d/dap.gal.yml`

```yaml
http:

  routers:

    public:
      entryPoints:
        - web
      rule: "Host(`dap.gal`) || Host(`www.dap.gal`)"
      service: svc-whost

    dns:
      entryPoints:
        - websecure
      rule: "Host(`dns.dap.gal`)"
      service: svc-dns
      middlewares:
        - redirect-admin
      tls:
        certResolver: cloudflare

    proxy:
      entryPoints:
        - websecure
      rule: "Host(`proxy.dap.gal`)"
      service: svc-proxy
      tls:
        certResolver: cloudflare

    stats:
      entryPoints:
        - websecure
      rule: "Host(`stats.dap.gal`)"
      service: svc-stats
      tls:
        certResolver: cloudflare

    home:
      entryPoints:
        - websecure
      rule: "Host(`home.dap.gal`)"
      service: svc-home
      tls:
        certResolver: cloudflare

  services:
    svc-whost:
      loadBalancer:
        servers:
          - url: "http://192.168.1.40:80"

    svc-dns:
      loadBalancer:
        servers:
          - url: "http://192.168.1.20"

    svc-proxy:
      loadBalancer:
        servers:
          - url: "http://192.168.1.31:8888"

    svc-stats:
      loadBalancer:
        servers:
          - url: "http://192.168.1.32:3000"

    svc-home:
      loadBalancer:
        servers:
          - url: "http://192.168.1.33:3000"

  middlewares:
    redirect-admin:
      redirectRegex:
        regex: "^https://dns\\.dap\\.gal/?$"
        replacement: "https://dns.dap.gal/admin/"
        permanent: false
```

---

## 8. Servicio systemd

### `/etc/systemd/system/traefik.service`

```ini
[Unit]
Description=Traefik
After=network.target

[Service]
EnvironmentFile=/etc/traefik/env/cloudflare.env
ExecStart=/usr/local/bin/traefik --configFile=/etc/traefik/traefik.yml
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable traefik
systemctl start traefik
```

---

## 9. Comandos Útiles

```bash
# Estado del servicio
systemctl status traefik

# Reiniciar (necesario tras cambios en traefik.yml;
# conf.d/ se recarga automáticamente)
systemctl restart traefik

# Ver rutas activas via API
curl -s http://localhost:8888/api/http/routers | jq '.[].rule'

# Ver servicios activos
curl -s http://localhost:8888/api/http/services | jq '.[].name'

# Verificar estado general
curl -s http://localhost:8888/api/overview | jq .

# Ver logs en tiempo real
tail -f /var/log/traefik/traefik.log
tail -f /var/log/traefik/access.log

# Comprobar que Traefik escucha en los puertos correctos
ss -tlnp | grep traefik

# Verificar certificados ACME
cat /etc/traefik/acme.json | jq '.cloudflare.Certificates[].domain'
```

---

## 10. Monitorización

Como en el resto de contenedores, el **Node Exporter** envía métricas a Grafana automáticamente.

```bash
# Últimas 20 líneas de cada log
tail -20 /var/log/traefik/traefik.log
tail -20 /var/log/traefik/access.log
```

> El dashboard de Traefik es accesible en LAN en `http://proxy.dap.gal`.