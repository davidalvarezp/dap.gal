# CT srv-01-ct-whost: Web Hosting

Contenedor dedicado a servir el sitio web estático **dap.gal** mediante **nginx**. Recibe el tráfico desde el reverse proxy (Traefik) y permite la subida de ficheros vía **SFTP/SSH** con el usuario `dap`.

---

## 1. Despliegue del Contenedor

En el nodo Proxmox del M920x, creamos el contenedor Debian 12:

- **CPU** 1 socket
- **RAM** 512 MB
- **Disco** 8 GB
- **Red** 192.168.1.40

---

## 2. Preparación del Sistema

```bash
# nginx
apt update && apt install -y nginx
systemctl enable nginx
systemctl start nginx

# SSH para despliegue de ficheros
apt install -y openssh-server

# Usuario de despliegue (sin sudo, solo web)
useradd -m -s /bin/bash dap
passwd dap

# Directorio SSH del usuario
mkdir -p /home/dap/.ssh
chmod 700 /home/dap/.ssh
```

---

## 3. Estructura de Ficheros

```
/var/www/
└── dap.gal/                 ← Raíz del sitio web
    ├── index.html
    └── ...                  ← Contenido estático del sitio

/etc/nginx/
├── sites-available/
│   └── dap.gal              ← Configuración del virtualhost
└── sites-enabled/
    └── dap.gal → ...        ← Enlace simbólico al anterior

/home/dap/
└── .ssh/                    ← Claves SSH para despliegue
```

---

## 4. Servicios y Cuentas

| Servicio | Detalle | Descripción |
|---|---|---|
| **nginx** | systemd service | Servidor web |
| **openssh-server** | puerto 22 | Acceso SFTP/SSH para despliegue |
| **Usuario `dap`** | `/var/www/dap.gal` | Propietario de los ficheros del sitio |
| **Sitio** | dap.gal / www.dap.gal | Dominio servido |
| **Tráfico entrante** | 192.168.1.31 (Traefik) | Único origen de peticiones HTTP |

---

## 5. Flujo de Tráfico

```
Cloudflare / LAN
      │
      │ HTTP → :8080 (internet) o :80 (LAN)
      ▼
CT srv-01-ct-proxy (Traefik)
      │
      │ HTTP → 192.168.1.40:80
      ▼
CT srv-01-ct-whost (nginx)
      │
      ▼
/var/www/dap.gal/index.html
```

```
Administrador
      │
      │ SFTP/SSH → 192.168.1.40:22 (usuario: dap)
      ▼
/var/www/dap.gal/           ← Subida de ficheros del sitio
```

---

## 6. Configuración nginx

### `/etc/nginx/sites-available/dap.gal`

```nginx
server {
    listen 80;
    server_name dap.gal www.dap.gal;

    root /var/www/dap.gal;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }

    access_log /var/log/nginx/dap.gal.access.log;
    error_log  /var/log/nginx/dap.gal.error.log;
}
```

```bash
# Activar el virtualhost y deshabilitar el default
ln -s /etc/nginx/sites-available/dap.gal /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Verificar sintaxis y recargar
nginx -t && systemctl reload nginx
```

---

## 7. Permisos del Directorio Web

```bash
# Propietario: dap (despliega) | grupo: www-data (nginx lee)
chown -R dap:www-data /var/www/dap.gal

# Directorios: rwxr-xr-x (nginx puede listar)
find /var/www/dap.gal -type d -exec chmod 755 {} \;

# Ficheros: rw-r--r-- (nginx puede leer, no ejecutar)
find /var/www/dap.gal -type f -exec chmod 644 {} \;
```

| Ruta | Propietario | Permisos |
|---|---|---|
| `/var/www/dap.gal/` (dirs) | `dap:www-data` | `755` |
| `/var/www/dap.gal/` (files) | `dap:www-data` | `644` |
| `/home/dap/.ssh/` | `dap:dap` | `700` |

---

## 8. Configuración SSH

### `/etc/ssh/sshd_config` (fragmento relevante)

```
PasswordAuthentication yes       # o no si se usa solo clave pública
PermitRootLogin no
AllowUsers dap
```

```bash
systemctl restart ssh
```

> Para despliegue con clave pública, añadir la clave pública del cliente en `/home/dap/.ssh/authorized_keys` con permisos `600`.

---

## 9. Despliegue de Ficheros

Desde la máquina de desarrollo, subir el sitio por SFTP:

```bash
# Subida con rsync (recomendado)
rsync -avz --delete ./dist/ dap@192.168.1.40:/var/www/dap.gal/

# O con scp para ficheros sueltos
scp index.html dap@192.168.1.40:/var/www/dap.gal/

# O con cliente SFTP (FileZilla, Cyberduck, etc.)
# Host: 192.168.1.40 | Puerto: 22 | Usuario: dap
```

---

## 10. Comandos Útiles

```bash
# Estado del servicio
systemctl status nginx

# Recargar configuración sin cortar conexiones
nginx -t && systemctl reload nginx

# Ver árbol del sitio
tree /var/www/dap.gal

# Ver logs en tiempo real
tail -f /var/log/nginx/dap.gal.access.log
tail -f /var/log/nginx/dap.gal.error.log

# Verificar que nginx escucha en el puerto 80
ss -tlnp | grep nginx

# Comprobar respuesta local
curl -H "Host: dap.gal" http://localhost
```

---

## 11. Monitorización

Como en el resto de contenedores, el **Node Exporter** envía métricas a Grafana automáticamente.

```bash
# Últimas 20 líneas de cada log
tail -20 /var/log/nginx/dap.gal.access.log
tail -20 /var/log/nginx/dap.gal.error.log
```