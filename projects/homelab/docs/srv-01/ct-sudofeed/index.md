# CT SudoFeed: Automatización de Contenido

Contenedor dedicado a la publicación automatizada de noticias tecnológicas en **Blogger**, **Telegram** y **Twitter/X**, con redacción de artículos mediante LLM local.

## 1. Despliegue del Contenedor

En el nodo Proxmox del M920x, creamos el contenedor debian 12:

- CPU 4 sockets (o unlimited)
- RAM 6 GB (6144mb)
- Disk 20 GB
- Red 192.168.1.98

## 2. Preparación del Sistema

```bash
# Actualización
apt update && apt upgrade -y

# Zona horaria
timedatectl set-timezone Europe/Madrid

# Locale español de España
apt install -y locales
sed -i 's/# es_ES.UTF-8 UTF-8/es_ES.UTF-8 UTF-8/' /etc/locale.gen
locale-gen
update-locale LANG=es_ES.UTF-8

# Dependencias Python
apt install -y python3 python3-pip curl python3-bs4 python3-lxml
pip3 install feedparser requests tweepy google-auth google-auth-oauthlib google-api-python-client beautifulsoup4 lxml --break-system-packages

# Ollama (servidor LLM local)
curl -fsSL https://ollama.com/install.sh | sh
systemctl enable ollama
systemctl start ollama

# Modelo LLM
ollama pull qwen2.5:7b
```

## 3. Estructura de Ficheros

```
/opt/sudofeed/
├── blogger/
│   ├── bot_blogger.py       ← Publica artículos en Blogger cada hora
│   ├── credentials.json     ← Credenciales OAuth2 de Google Cloud
│   ├── token.json           ← Token de acceso a la Blogger API
│   └── historial.json       ← Control de noticias ya publicadas
├── telegram/
│   ├── bot_tg.py            ← Publica en canal @sudoFeedES
│   └── historial_tg.json    ← Control de posts ya enviados
└── twitter/
    ├── bot_tw.py            ← Publica tweets en @SudoFeedES
    └── historial_tw.json    ← Control de tweets ya enviados
```

## 4. Servicios y Cuentas

| Servicio | Cuenta | Descripción |
|---|---|---|
| **Blogger** | sudofeed.blogspot.com | Blog principal, fuente de contenido |
| **Telegram** | @sudoFeedES | Canal de difusión |
| **Twitter/X** | @SudoFeedES | Cuenta de Twitter |
| **Ollama** | localhost:11434 | Servidor LLM local |
| **Modelo LLM** | qwen2.5:7b | Redacción de artículos en español |
| **Google Cloud** | Proyecto SudoFeed | Blogger API v3 |

## 5. Flujo de Publicación

```
RSS feeds (inglés)
       ↓
Ollama gemma3:4b redacta artículo en español de España
       ↓
Blogger API publica entrada (cada hora en punto)
       ↓
bot_tg.py coge último post del blog → publica resumen + enlace en Telegram (a y 30)
bot_tw.py coge último post del blog → publica tweet sin enlace en Twitter (a y 30)
```

## 6. Fuentes RSS por Categoría

| Categoría | Fuentes |
|---|---|
| Noticias IT | The Hacker News, Dark Reading |
| Ciberseguridad | The Hacker News, Krebs on Security, WeLiveSecurity |
| Vulnerabilidades | Dark Reading, SANS ISC |
| Linux | OMG Linux, It's FOSS |
| Software | It's FOSS, OMG Linux |
| IA y Tecnología | The Hacker News, Dark Reading |
| Herramientas Hacking | WeLiveSecurity, SANS ISC |

## 7. Configuración del Cron

```bash
crontab -e
```

```
# BLOGGER — cada hora en punto
0 * * * * python3 /opt/sudofeed/blogger/bot_blogger.py >> /opt/sudofeed/blogger/blogger.log 2>&1

# TELEGRAM — a y 30
30  8 * * * python3 /opt/sudofeed/telegram/bot_tg.py >> /opt/sudofeed/telegram/telegram.log 2>&1
30 10 * * * python3 /opt/sudofeed/telegram/bot_tg.py >> /opt/sudofeed/telegram/telegram.log 2>&1
30 12 * * * python3 /opt/sudofeed/telegram/bot_tg.py >> /opt/sudofeed/telegram/telegram.log 2>&1
30 14 * * * python3 /opt/sudofeed/telegram/bot_tg.py >> /opt/sudofeed/telegram/telegram.log 2>&1
30 17 * * * python3 /opt/sudofeed/telegram/bot_tg.py >> /opt/sudofeed/telegram/telegram.log 2>&1
30 19 * * * python3 /opt/sudofeed/telegram/bot_tg.py >> /opt/sudofeed/telegram/telegram.log 2>&1
30 21 * * * python3 /opt/sudofeed/telegram/bot_tg.py >> /opt/sudofeed/telegram/telegram.log 2>&1
30 23 * * * python3 /opt/sudofeed/telegram/bot_tg.py >> /opt/sudofeed/telegram/telegram.log 2>&1

# TWITTER — a y 30
30 10 * * * python3 /opt/sudofeed/twitter/bot_tw.py >> /opt/sudofeed/twitter/twitter.log 2>&1
30 12 * * * python3 /opt/sudofeed/twitter/bot_tw.py >> /opt/sudofeed/twitter/twitter.log 2>&1
30 14 * * * python3 /opt/sudofeed/twitter/bot_tw.py >> /opt/sudofeed/twitter/twitter.log 2>&1
30 19 * * * python3 /opt/sudofeed/twitter/bot_tw.py >> /opt/sudofeed/twitter/twitter.log 2>&1
30 21 * * * python3 /opt/sudofeed/twitter/bot_tw.py >> /opt/sudofeed/twitter/twitter.log 2>&1
```

## 8. Credenciales Google Cloud

La autenticación OAuth2 con la Blogger API requiere dos ficheros en `/opt/sudofeed/blogger/`:

- `credentials.json` → descargado desde [console.cloud.google.com](https://console.cloud.google.com) → proyecto SudoFeed → APIs y servicios → Credenciales
- `token.json` → generado ejecutando `auth.py` en un ordenador con navegador

El token se renueva automáticamente cuando caduca. Si falla la autenticación regenerar desde Google Cloud Console.

## 9. Comandos Útiles

```bash
# Forzar publicación manual en Blogger
python3 -c "
import sys; sys.path.insert(0, '/opt/sudofeed/blogger')
import bot_blogger
bot_blogger.HORARIO[$(date +%H | sed 's/^0//')] = 'ciberseguridad'
bot_blogger.main()
"

# Forzar publicación manual en Telegram
python3 -c "
import sys; sys.path.insert(0, '/opt/sudofeed/telegram')
import bot_tg
bot_tg.HORARIO[$(date +%H | sed 's/^0//')] = 'ciberseguridad'
bot_tg.main()
"

# Forzar publicación manual en Twitter
python3 -c "
import sys; sys.path.insert(0, '/opt/sudofeed/twitter')
import bot_tw
bot_tw.HORARIO[$(date +%H | sed 's/^0//')] = 'ciberseguridad'
bot_tw.main()
"

# Ver logs en tiempo real
tail -f /opt/sudofeed/blogger/blogger.log
tail -f /opt/sudofeed/telegram/telegram.log
tail -f /opt/sudofeed/twitter/twitter.log

# Estado del servicio Ollama
systemctl status ollama

# Ver modelos instalados
ollama list
```

## 10. Monitorización

Como en el resto de contenedores, el **Node Exporter** envía métricas a Grafana automáticamente.

Para revisar el estado de las publicaciones:

```bash
# Últimas 20 líneas de cada log
tail -20 /opt/sudofeed/blogger/blogger.log
tail -20 /opt/sudofeed/telegram/telegram.log
tail -20 /opt/sudofeed/twitter/twitter.log
```