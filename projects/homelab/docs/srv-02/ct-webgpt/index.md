# CT srv-01-ct-webgpt: Interfaz Web LLM

Contenedor dedicado a ejecutar **Open WebUI**, una interfaz web tipo ChatGPT que conecta contra el servidor Ollama del homelab. Permite interactuar con los modelos LLM locales desde el navegador, sin enviar datos a servicios externos.

---

## 1. Despliegue del Contenedor

En el nodo **srv-01** (Lenovo M920x Tiny), creamos el contenedor Debian 12:

- **CPU** 2 sockets
- **RAM** 1 GB
- **Disco** 8 GB
- **Red** 192.168.1.XX *(completar)*

---

## 2. Preparación del Sistema

```bash
# Actualización base
apt update && apt upgrade -y
apt install -y curl ca-certificates gnupg

# Instalar Docker (repositorio oficial)
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg \
    -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.asc] \
    https://download.docker.com/linux/debian bookworm stable" \
    > /etc/apt/sources.list.d/docker.list

apt update && apt install -y docker-ce docker-ce-cli containerd.io

systemctl enable docker
systemctl start docker

# Verificar
docker --version
```

---

## 3. Estructura de Ficheros

```
/var/lib/docker/volumes/
└── open-webui/              ← Volumen persistente con base de datos,
    └── _data/               ← usuarios, conversaciones y configuración
```

---

## 4. Servicios

| Servicio | Puerto | Descripción |
|---|---|---|
| **Docker** | — | Runtime de contenedores |
| **open-webui** (contenedor) | 3000 → 8080 | Interfaz web LLM |
| **openssh-server** | 22 TCP | Acceso administrativo |

---

## 5. Flujo de Uso

```
Usuario (LAN)
      │
      │ HTTP → 192.168.1.XX:3000
      │     (o via Traefik → webgpt.dap.gal)
      ▼
CT srv-01-ct-webgpt
  Docker: open-webui:main
      │
      │ HTTP → 192.168.1.98:11434  (Ollama API)
      ▼
CT srv-01-ct-sudofeed (Ollama)
      │
      ▼
Modelo LLM local (qwen2.5:7b u otros)
```

> El backend LLM apunta actualmente a `192.168.1.98` (Ollama de `srv-01-ct-sudofeed`).  
> Si se quiere usar el CT dedicado `srv-02-ct-llm`, cambiar `OLLAMA_BASE_URL`.

---

## 6. Despliegue del Contenedor Docker

```bash
docker run -d \
    --name open-webui \
    --restart always \
    -p 3000:8080 \
    -e OLLAMA_BASE_URL=http://192.168.1.98:11434 \
    -v open-webui:/app/backend/data \
    ghcr.io/open-webui/open-webui:main
```

| Parámetro | Valor | Descripción |
|---|---|---|
| `--restart always` | — | Arranca automáticamente con el CT |
| `-p 3000:8080` | host:contenedor | Puerto de acceso web |
| `OLLAMA_BASE_URL` | `http://192.168.1.98:11434` | Ollama backend |
| `-v open-webui:...` | volumen Docker | Persistencia de datos |

---

## 7. Integración con Traefik (opcional)

Para acceder via subdominio en lugar de por IP:port, añadir en `/etc/traefik/conf.d/dap.gal.yml` del CT proxy:

```yaml
    webgpt:
      entryPoints:
        - lan
      rule: "Host(`webgpt.dap.gal`)"
      service: svc-webgpt

    svc-webgpt:
      loadBalancer:
        servers:
          - url: "http://192.168.1.XX:3000"
```

---

## 8. Monitorización

> **Node Exporter no aparece en el historial** — pendiente de confirmar si está instalado.

```bash
# Instalar si no está
apt install -y prometheus-node-exporter
systemctl enable prometheus-node-exporter
systemctl start prometheus-node-exporter
```

Expone métricas en `http://192.168.1.XX:9100/metrics`.

---

## 9. Comandos Útiles

```bash
# Estado del contenedor Docker
docker ps
docker ps -a   # incluye parados

# Logs de Open WebUI en tiempo real
docker logs -f open-webui

# Últimas 50 líneas de log
docker logs --tail 50 open-webui

# Reiniciar Open WebUI
docker restart open-webui

# Parar / arrancar
docker stop open-webui
docker start open-webui

# Actualizar a la última imagen
docker pull ghcr.io/open-webui/open-webui:main
docker stop open-webui && docker rm open-webui
# → volver a ejecutar el docker run de la sección 6

# Ver volúmenes Docker
docker volume ls
docker volume inspect open-webui

# Uso de recursos del contenedor
docker stats open-webui

# Verificar conectividad con Ollama
curl http://192.168.1.98:11434/api/version
```

---

## 10. Lo que falta documentar / configurar

### Pendiente de completar en este documento
- **IP del CT** — no visible en el historial; completar en secciones 1, 5 y 7
- **Ruta Traefik** — no hay entrada en `dap.gal.yml` para este CT; acceso actualmente solo por IP:3000
- **Node Exporter** — no confirmado; verificar con `systemctl status prometheus-node-exporter`

### Pendiente de configurar
- **Cambiar `OLLAMA_BASE_URL`** a `srv-02-ct-llm` si se quiere usar el CT LLM dedicado en lugar del de SudoFeed
- **Ruta Traefik** — sin subdominio propio; solo accesible por IP directa
- **Autenticación** — Open WebUI pide crear cuenta admin en el primer acceso; verificar que está configurada
- **UFW** — sin reglas de cortafuegos en el CT