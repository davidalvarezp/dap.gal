# Guía Profesional: Blog Técnico con Ghost en Debian 13 (LXC Proxmox)

> **Stack:** Proxmox VE → LXC Debian 13 → Ghost CMS → MySQL 8 → Nginx → Reverse Proxy externo
> **Nivel:** Desde cero, paso a paso, con explicaciones de qué hace cada cosa y por qué.

---

## Índice

1. [Preparar el contenedor LXC en Proxmox](#1-preparar-el-contenedor-lxc-en-proxmox)
2. [Sistema base: Debian 13 hardening mínimo](#2-sistema-base-debian-13-hardening-mínimo)
3. [Instalar Node.js (vía nvm)](#3-instalar-nodejs-vía-nvm)
4. [Instalar y configurar MySQL 8](#4-instalar-y-configurar-mysql-8)
5. [Instalar Nginx (proxy interno)](#5-instalar-nginx-proxy-interno)
6. [Instalar Ghost CLI y Ghost](#6-instalar-ghost-cli-y-ghost)
7. [Configuración de producción de Ghost](#7-configuración-de-producción-de-ghost)
8. [Integrar con tu reverse proxy externo](#8-integrar-con-tu-reverse-proxy-externo)
9. [SSL, seguridad y cabeceras HTTP](#9-ssl-seguridad-y-cabeceras-http)
10. [Backups automáticos](#10-backups-automáticos)
11. [Mantenimiento y actualización de Ghost](#11-mantenimiento-y-actualización-de-ghost)
12. [Estructura del blog técnico: primeros pasos](#12-estructura-del-blog-técnico-primeros-pasos)
13. [Temas recomendados para blogs técnicos](#13-temas-recomendados-para-blogs-técnicos)
14. [Integraciones útiles para sysadmin/cybersec](#14-integraciones-útiles-para-sysadmincybersec)
15. [Troubleshooting frecuente](#15-troubleshooting-frecuente)

---

## 1. Preparar el contenedor LXC en Proxmox

### 1.1 Descargar la plantilla de Debian 13

En el shell de Proxmox (nodo):

```bash
# Actualizar la lista de plantillas disponibles
pveam update

# Buscar Debian 13 (bookworm/trixie según versión)
pveam available | grep debian

# Descargar la plantilla (ajusta el storage según tu setup)
pveam download local debian-13-standard_13.0-1_amd64.tar.zst
```

### 1.2 Crear el contenedor LXC

Desde la GUI de Proxmox o por CLI:

```bash
# Por CLI (ajusta los valores a tu entorno)
pct create 200 local:vztmpl/debian-13-standard_13.0-1_amd64.tar.zst \
  --hostname ghost-blog \
  --memory 2048 \
  --swap 512 \
  --cores 2 \
  --rootfs local-lvm:20 \
  --net0 name=eth0,bridge=vmbr0,ip=192.168.1.200/24,gw=192.168.1.1 \
  --nameserver 1.1.1.1 \
  --unprivileged 1 \
  --features nesting=1 \
  --password 'TuPasswordSegura123!'
```

> **¿Por qué estos parámetros?**
> - `--unprivileged 1`: El contenedor corre sin privilegios de root del host. Más seguro.
> - `--features nesting=1`: Necesario si quieres correr Docker dentro (opcional, aquí no lo usaremos).
> - `--memory 2048`: Ghost + MySQL + Nginx mínimo recomendado. Con 1GB funciona, pero con picos puede fallar.

### 1.3 Arrancar y conectarse

```bash
pct start 200
pct enter 200
```

---

## 2. Sistema base: Debian 13 hardening mínimo

### 2.1 Actualizar el sistema

```bash
apt update && apt upgrade -y
apt install -y curl wget git unzip nano sudo ufw fail2ban logrotate
```

### 2.2 Crear usuario no-root para Ghost

Ghost **no puede correr como root**. La CLI lo bloquea por seguridad.

```bash
# Crear usuario dedicado
adduser ghost-admin
# Contraseña segura cuando te la pida

# Añadirlo a sudo (para instalar dependencias)
usermod -aG sudo ghost-admin

# Cambiar a ese usuario para el resto de la instalación
su - ghost-admin
```

### 2.3 Configurar UFW (firewall)

```bash
# Como root o con sudo
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP (necesario para Ghost y Nginx)
sudo ufw allow 443/tcp     # HTTPS
sudo ufw enable
sudo ufw status
```

> **Nota:** Si tu reverse proxy externo está en otra máquina de la misma red, puedes restringir el 80/443 solo a esa IP:
> `sudo ufw allow from 192.168.1.x to any port 80`

### 2.4 Configurar Fail2ban básico

```bash
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local

# Editar configuración básica
sudo nano /etc/fail2ban/jail.local
```

Busca y ajusta en `[DEFAULT]`:

```ini
bantime  = 1h
findtime  = 10m
maxretry = 5
```

```bash
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

---

## 3. Instalar Node.js (vía nvm)

Ghost requiere Node.js. La versión compatible con Ghost 5.x es **Node 18.x o 20.x LTS**.

> **¿Por qué nvm?** Porque Ghost CLI es muy estricta con versiones. Si en el futuro necesitas cambiar, nvm te lo pone fácil sin romper el sistema.

```bash
# Como ghost-admin
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

# Recargar el shell
source ~/.bashrc
# o cerrar y volver a entrar: exit → su - ghost-admin

# Verificar que nvm funciona
nvm --version

# Instalar Node 20 LTS (compatible con Ghost 5.x)
nvm install 20
nvm use 20
nvm alias default 20

# Verificar
node --version   # debe mostrar v20.x.x
npm --version
```

---

## 4. Instalar y configurar MySQL 8

Ghost soporta MySQL y SQLite. **Para producción, usa MySQL.** SQLite es solo para desarrollo.

```bash
sudo apt install -y mysql-server

# Arrancar y habilitar
sudo systemctl enable mysql
sudo systemctl start mysql

# Securización inicial (responde a las preguntas)
sudo mysql_secure_installation
```

En `mysql_secure_installation`:
- **Validate password component**: Sí (nivel MEDIUM como mínimo)
- **Remove anonymous users**: Sí
- **Disallow root login remotely**: Sí
- **Remove test database**: Sí
- **Reload privilege tables**: Sí

### 4.1 Crear base de datos y usuario para Ghost

```bash
sudo mysql -u root -p
```

```sql
-- Crear la base de datos
CREATE DATABASE ghostdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Crear usuario dedicado (NO uses root para Ghost)
CREATE USER 'ghostuser'@'localhost' IDENTIFIED BY 'TuPasswordDB_MuySegura!';

-- Dar permisos solo sobre la DB de Ghost
GRANT ALL PRIVILEGES ON ghostdb.* TO 'ghostuser'@'localhost';

-- Aplicar cambios
FLUSH PRIVILEGES;

-- Verificar
SHOW DATABASES;
EXIT;
```

> **Seguridad:** El usuario `ghostuser` solo tiene acceso a `ghostdb` y solo desde localhost. Si alguien compromete Ghost, no puede tocar otras bases de datos.

---

## 5. Instalar Nginx (proxy interno)

Ghost corre en el puerto 2368. Nginx actúa de proxy local hacia ese puerto y es lo que Ghost CLI configura automáticamente.

```bash
sudo apt install -y nginx

sudo systemctl enable nginx
sudo systemctl start nginx

# Verificar que funciona
curl -I http://localhost
# Debes ver: HTTP/1.1 200 OK
```

---

## 6. Instalar Ghost CLI y Ghost

### 6.1 Instalar Ghost CLI globalmente

```bash
# Como ghost-admin (con nvm activo)
npm install -g ghost-cli

# Verificar
ghost --version
```

### 6.2 Crear el directorio de instalación

```bash
# Ghost CLI es muy exigente: el directorio debe estar vacío y ser propiedad del usuario
sudo mkdir -p /var/www/ghost
sudo chown ghost-admin:ghost-admin /var/www/ghost
sudo chmod 755 /var/www/ghost

cd /var/www/ghost
```

### 6.3 Instalar Ghost

```bash
ghost install
```

La CLI te hará una serie de preguntas. Aquí las respuestas correctas:

```
? Enter your blog URL: https://tublog.tudominio.com
? Enter your MySQL hostname: localhost
? Enter your MySQL username: ghostuser
? Enter your MySQL password: [la que pusiste antes]
? Enter your Ghost database name: ghostdb
? Do you wish to set up Nginx? Yes
? Do you wish to set up SSL? No
  (TU REVERSE PROXY YA GESTIONA EL SSL)
? Do you wish to set up Systemd? Yes
? Do you want to start Ghost? Yes
```

> **¡Importante!** Cuando te pregunte por SSL di **No**. Tu reverse proxy externo ya maneja los certificados. Si dices Sí, Ghost intentará usar Certbot y fallará (o creará conflictos).

### 6.4 Verificar que Ghost está corriendo

```bash
ghost status
# Debe mostrar: ✔ Ghost is running

# También puedes ver el proceso
ps aux | grep ghost

# Y el log en tiempo real
ghost log
```

---

## 7. Configuración de producción de Ghost

El archivo de configuración principal está en:

```bash
cat /var/www/ghost/config.production.json
```

Debería verse así (ajusta según tu setup):

```json
{
  "url": "https://tublog.tudominio.com",
  "server": {
    "port": 2368,
    "host": "127.0.0.1"
  },
  "database": {
    "client": "mysql8",
    "connection": {
      "host": "localhost",
      "port": 3306,
      "user": "ghostuser",
      "password": "TuPasswordDB_MuySegura!",
      "database": "ghostdb"
    }
  },
  "mail": {
    "transport": "SMTP",
    "options": {
      "service": "Mailgun",
      "host": "smtp.mailgun.org",
      "port": 587,
      "auth": {
        "user": "postmaster@mg.tudominio.com",
        "pass": "tu_api_key_mailgun"
      }
    }
  },
  "logging": {
    "transports": ["file", "stdout"]
  },
  "process": "systemd",
  "paths": {
    "contentPath": "/var/www/ghost/content"
  }
}
```

> **Email:** Para que funcionen los magic links de login, newsletters y notificaciones, necesitas SMTP. Mailgun tiene un tier gratuito generoso. Sendgrid y Brevo también funcionan.

### 7.1 Editar configuración si necesitas cambios

```bash
# Editar directamente (luego reiniciar Ghost)
nano /var/www/ghost/config.production.json
ghost restart
```

O usando la CLI:

```bash
ghost config url https://tublog.tudominio.com
ghost restart
```

---

## 8. Integrar con tu reverse proxy externo

Ghost CLI ya configuró un Nginx local en `/etc/nginx/sites-available/`. Este Nginx escucha en el puerto 80 del contenedor y hace proxy al puerto 2368 donde corre Ghost.

Tu stack completo es:

```
Internet → Reverse Proxy (Nginx/Traefik/Caddy externo con SSL) 
        → http://192.168.1.200:80 (Nginx interno del contenedor)
        → http://127.0.0.1:2368 (Ghost)
```

### 8.1 Ver la configuración de Nginx que generó Ghost CLI

```bash
cat /etc/nginx/sites-available/tublog.tudominio.com
```

### 8.2 Configuración en tu reverse proxy externo

**Si usas Nginx Proxy Manager (NPM):**

1. Añade un nuevo Proxy Host
2. **Domain Names:** `tublog.tudominio.com`
3. **Scheme:** `http`
4. **Forward Hostname/IP:** `192.168.1.200` (IP del contenedor)
5. **Forward Port:** `80`
6. Activa: **Block Common Exploits**, **Websockets Support**
7. En la pestaña SSL: selecciona tu certificado o pide uno nuevo con Let's Encrypt

**Cabeceras importantes que debe pasar el reverse proxy:**

```nginx
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header Host $host;
```

En NPM estas se añaden en la pestaña **Advanced** si no las pone automáticamente.

**Si usas Traefik:**

```yaml
# docker-compose labels o traefik.yml
http:
  routers:
    ghost:
      rule: "Host(`tublog.tudominio.com`)"
      entrypoints:
        - websecure
      tls:
        certResolver: letsencrypt
      service: ghost

  services:
    ghost:
      loadBalancer:
        servers:
          - url: "http://192.168.1.200:80"
```

**Si usas Caddy:**

```
tublog.tudominio.com {
    reverse_proxy 192.168.1.200:80
}
```

### 8.3 Decirle a Ghost que está detrás de un proxy

```bash
# Editar config
nano /var/www/ghost/config.production.json
```

Añade/verifica que `url` es el dominio público con HTTPS:

```json
"url": "https://tublog.tudominio.com"
```

Y opcionalmente, si tienes problemas con IPs:

```json
"server": {
  "port": 2368,
  "host": "127.0.0.1"
},
"trustedProxies": ["loopback", "linklocal", "uniquelocal"]
```

```bash
ghost restart
```

---

## 9. SSL, seguridad y cabeceras HTTP

### 9.1 Cabeceras de seguridad HTTP

Añade en tu reverse proxy externo (o en el Nginx del contenedor):

```nginx
# Evita clickjacking
add_header X-Frame-Options "SAMEORIGIN" always;

# Evita que el navegador "adivine" el content-type
add_header X-Content-Type-Options "nosniff" always;

# Referrer policy
add_header Referrer-Policy "strict-origin-when-cross-origin" always;

# Permissions policy
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;

# HSTS (solo si estás 100% seguro de usar HTTPS siempre)
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

# Content Security Policy (ajústalo a tu tema de Ghost)
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:;" always;
```

> **Nota:** El CSP necesita ajuste fino según el tema que uses. Empieza sin él y añádelo cuando el blog esté funcionando bien.

### 9.2 Verificar la seguridad

Cuando el blog esté en marcha, analízalo con:

- **https://securityheaders.com** → Cabeceras HTTP
- **https://www.ssllabs.com/ssltest/** → Calidad del certificado SSL
- **https://observatory.mozilla.org** → Análisis completo

---

## 10. Backups automáticos

### 10.1 Backup de MySQL

```bash
# Crear script de backup
sudo nano /opt/backup-ghost.sh
```

```bash
#!/bin/bash

# Configuración
DB_USER="ghostuser"
DB_PASS="TuPasswordDB_MuySegura!"
DB_NAME="ghostdb"
BACKUP_DIR="/opt/backups/ghost"
GHOST_CONTENT="/var/www/ghost/content"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Crear directorio si no existe
mkdir -p "$BACKUP_DIR"

# Backup de la base de datos
mysqldump -u"$DB_USER" -p"$DB_PASS" "$DB_NAME" | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

# Backup del contenido (imágenes, temas, etc.)
tar -czf "$BACKUP_DIR/content_$DATE.tar.gz" -C "$(dirname $GHOST_CONTENT)" "$(basename $GHOST_CONTENT)"

# Backup de la configuración
cp /var/www/ghost/config.production.json "$BACKUP_DIR/config_$DATE.json"

# Limpiar backups viejos
find "$BACKUP_DIR" -type f -mtime +$RETENTION_DAYS -delete

echo "[$DATE] Backup completado en $BACKUP_DIR"
```

```bash
sudo chmod +x /opt/backup-ghost.sh
sudo mkdir -p /opt/backups/ghost

# Probar manualmente
sudo /opt/backup-ghost.sh

# Programar con cron (todos los días a las 3am)
sudo crontab -e
```

Añadir:

```cron
0 3 * * * /opt/backup-ghost.sh >> /var/log/ghost-backup.log 2>&1
```

### 10.2 Snapshot de Proxmox (desde el host)

La forma más segura: snapshot del contenedor completo antes de actualizaciones.

```bash
# En el nodo de Proxmox (no dentro del contenedor)
pct snapshot 200 pre-update-$(date +%Y%m%d) --description "Antes de actualizar Ghost"

# Listar snapshots
pct listsnapshot 200

# Restaurar si algo sale mal
pct rollback 200 pre-update-20241201
```

---

## 11. Mantenimiento y actualización de Ghost

### 11.1 Comandos esenciales de Ghost CLI

```bash
# Estado
ghost status

# Arrancar / Parar / Reiniciar
ghost start
ghost stop
ghost restart

# Ver logs en tiempo real
ghost log
ghost log -f   # follow (como tail -f)

# Ver configuración actual
ghost config

# Ver versión instalada
ghost version
```

### 11.2 Actualizar Ghost

```bash
# SIEMPRE hacer backup/snapshot antes
pct snapshot 200 pre-update-$(date +%Y%m%d)  # desde el host Proxmox

# Dentro del contenedor, como ghost-admin
cd /var/www/ghost
ghost update

# Si algo falla, rollback
ghost update --rollback

# Para actualizar a una versión específica
ghost update --version 5.x.x
```

### 11.3 Actualizar el sistema operativo

```bash
sudo apt update && sudo apt upgrade -y

# Limpiar paquetes innecesarios
sudo apt autoremove -y
sudo apt autoclean
```

---

## 12. Estructura del blog técnico: primeros pasos

### 12.1 Acceder al panel de administración

Una vez todo funcionando:

```
https://tublog.tudominio.com/ghost
```

Crea tu cuenta de administrador (primera visita).

### 12.2 Estructura de contenido recomendada para técnicos

**Tags (etiquetas) sugeridas:**

| Tag | Uso |
|-----|-----|
| `#homelab` | Proyectos de laboratorio personal |
| `#proxmox` | Todo sobre Proxmox VE |
| `#docker` | Contenedores y compose |
| `#linux` | Sysadmin general |
| `#networking` | Redes, VLANs, pfSense... |
| `#cybersec` | Ciberseguridad ofensiva/defensiva |
| `#ctf` | Write-ups de CTFs |
| `#monitoring` | Grafana, Prometheus, alertas |
| `#automation` | Ansible, scripts, CI/CD |
| `#writeup` | Análisis técnicos en profundidad |

**Estructura de navegación sugerida:**

```
Inicio | Homelab | Ciberseguridad | CTF Write-ups | Sobre mí
```

En Ghost Admin → Design → Navigation.

### 12.3 Markdown y syntax highlighting

Ghost usa un editor de tarjetas (cards). Para código técnico:

- Usa la **Code Card** (bloque de código con syntax highlight automático)
- Para posts técnicos largos, considera escribir en Markdown con la opción de importar

**Shortcut útil:** `/` en el editor abre el menú de cards.

### 12.4 Configurar la página "Sobre mí"

Settings → General → Publication cover
Crea una página estática: New Page → "Sobre mí" → marca como página en la navegación.

---

## 13. Temas recomendados para blogs técnicos

### Gratuitos

| Tema | Descripción | URL |
|------|-------------|-----|
| **Casper** | Default de Ghost, limpio y minimalista | Incluido |
| **Edition** | Enfocado a newsletters técnicas | Ghost marketplace |
| **Attila** | Oscuro, ideal para contenido técnico | GitHub |
| **Massively** | Imagen hero grande, buena tipografía | Ghost marketplace |

### De pago (valen la pena)

| Tema | Precio | Por qué |
|------|--------|---------|
| **Dope** | ~$49 | Oscuro, moderno, perfecto para tech |
| **Tinker** | ~$49 | Diseñado específicamente para blogs de devs |
| **Orca** | ~$39 | Minimalista, enfocado en lectura |

### Instalar un tema

```bash
# Descargar el .zip del tema
# En Ghost Admin → Design → Change theme → Upload theme

# O por CLI
cd /var/www/ghost/content/themes
unzip tu-tema.zip
ghost restart
```

### Dark mode para Casper (hack rápido)

Si usas Casper por defecto, añade en Ghost Admin → Design → Code Injection → Site Header:

```html
<style>
:root {
  --color-primary: #00d4ff;
}
</style>
```

---

## 14. Integraciones útiles para sysadmin/cybersec

### 14.1 Umami (Analytics sin cookies, auto-hosted)

Mejor que Google Analytics. Puedes hostearlo en otro contenedor.

```bash
# En Ghost Admin → Settings → Code Injection → Site Header
<script async defer data-website-id="TU-ID" src="https://analytics.tudominio.com/script.js"></script>
```

### 14.2 Algolia Search (búsqueda potente)

Ghost tiene búsqueda nativa desde v5.x. Si quieres más control:

```bash
ghost config --all | grep search
```

### 14.3 Webhooks para notificaciones

Ghost puede enviar webhooks cuando publicas un post:

Settings → Integrations → Add custom integration

Úsalo para:
- Enviar notificación a tu Discord/Slack personal
- Trigger en n8n para automatizar la distribución
- Notificar a un bot de Telegram

**Ejemplo: Notificación a Discord cuando publicas**

En n8n o directamente:

```bash
curl -X POST "https://discord.com/api/webhooks/TU_WEBHOOK" \
  -H "Content-Type: application/json" \
  -d '{"content": "🚀 Nuevo post publicado en el blog!"}'
```

### 14.4 Código de bloques con copy button

Añade esto en Code Injection → Site Footer:

```html
<script>
document.querySelectorAll('pre code').forEach(block => {
  const btn = document.createElement('button');
  btn.textContent = 'Copy';
  btn.style.cssText = 'position:absolute;top:5px;right:5px;padding:2px 8px;font-size:12px;cursor:pointer;';
  block.parentElement.style.position = 'relative';
  block.parentElement.appendChild(btn);
  btn.addEventListener('click', () => {
    navigator.clipboard.writeText(block.textContent);
    btn.textContent = '✓ Copied!';
    setTimeout(() => btn.textContent = 'Copy', 2000);
  });
});
</script>
```

### 14.5 RSS Feed

Ghost genera RSS automáticamente:

```
https://tublog.tudominio.com/rss/
https://tublog.tudominio.com/tag/homelab/rss/  ← por tag
```

Compártelo con tu comunidad y subscríbete con Feedly/Miniflux.

---

## 15. Troubleshooting frecuente

### Ghost no arranca

```bash
ghost log          # Ver el error específico
ghost doctor       # Diagnóstico automático de Ghost CLI
systemctl status ghost_tublog-tudominio-com   # Estado del servicio systemd
journalctl -u ghost_* -f   # Logs de systemd
```

### Error 502 Bad Gateway

```bash
# Verificar que Ghost está corriendo en el puerto 2368
ss -tlnp | grep 2368

# Verificar Nginx local
nginx -t
systemctl status nginx

# Verificar conectividad
curl -I http://localhost
curl -I http://127.0.0.1:2368
```

### Error de permisos

```bash
# Ghost debe ser propietario de su directorio
sudo chown -R ghost-admin:ghost-admin /var/www/ghost
```

### MySQL no conecta

```bash
# Verificar que MySQL corre
systemctl status mysql

# Probar credenciales manualmente
mysql -u ghostuser -p ghostdb

# Ver si escucha
ss -tlnp | grep 3306
```

### Ghost lento al arrancar en LXC

Añade en Proxmox → CT Options → Start/Shutdown → Start delay: 30 segundos. Ghost necesita que MySQL esté completamente listo antes de arrancar.

### Las imágenes no cargan o URLs incorrectas

```bash
# Verificar que la URL en config es correcta (con https://)
ghost config url
# Si no, corregir:
ghost config url https://tublog.tudominio.com
ghost restart
```

### El email no funciona (magic links)

```bash
# Test de email desde Ghost CLI
ghost config | grep mail

# Puedes probar con el SMTP de Gmail (menos recomendado para producción)
# o usar Brevo/Mailgun con su SMTP gratuito
```

---

## Checklist final de puesta en producción

```
[ ] Contenedor LXC arranca con Proxmox
[ ] Ghost corriendo: ghost status → running
[ ] MySQL operativo con usuario dedicado
[ ] Nginx local respondiendo en puerto 80
[ ] Reverse proxy externo enrutando correctamente
[ ] HTTPS funcionando en el dominio público
[ ] Panel de admin accesible en /ghost
[ ] Email SMTP configurado y probado
[ ] Backup automático configurado y probado
[ ] UFW activo con reglas mínimas
[ ] Fail2ban activo
[ ] Snapshot de Proxmox del estado inicial
[ ] Cabeceras de seguridad en el reverse proxy
[ ] Analytics configurado (Umami u otro)
[ ] DNS apuntando al reverse proxy
```

---

## Recursos adicionales

- **Documentación oficial Ghost:** https://ghost.org/docs/
- **Ghost Forum (comunidad activa):** https://forum.ghost.org
- **Ghost CLI Reference:** https://ghost.org/docs/ghost-cli/
- **Ghost Themes Marketplace:** https://ghost.org/marketplace/
- **Proxmox LXC Wiki:** https://pve.proxmox.com/wiki/Linux_Container

---

*Guía generada para stack: Proxmox VE + LXC Debian 13 + Ghost 5.x + MySQL 8 + Nginx*
*Última revisión: Mayo 2026*