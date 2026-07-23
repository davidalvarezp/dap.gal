# CT srv-02-ct-llm: Servidor LLM Local

Contenedor dedicado a ejecutar modelos de lenguaje local mediante **Ollama**, exponiendo una API REST para el resto de servicios del homelab. Actúa como backend LLM centralizado, desacoplado de los bots y automatizaciones que lo consumen.

---

## 1. Despliegue del Contenedor

En el nodo **srv-02** (Lenovo M920x Tiny), creamos el contenedor Debian 12:

- **CPU** *(completar — recomendado: 4+ cores)*
- **RAM** *(completar — recomendado: 8+ GB según modelos)*
- **Disco** 20 GB (rootfs ampliado con `pct resize`)
- **Red** 192.168.1.XX *(completar)*

> El disco fue redimensionado a 20 GB desde el host con `pct resize 198 rootfs 20G`.

---

## 2. Preparación del Sistema

```bash
# Actualización base
apt update && apt full-upgrade -y

# Dependencias
apt install -y curl bash-completion
echo "source /etc/bash_completion" >> ~/.bashrc
source ~/.bashrc
```

---

## 3. Instalación de Ollama

```bash
# Instalación oficial (no pasa por apt, instala el binario directamente)
curl -fsSL https://ollama.com/install.sh | sh

systemctl enable ollama
systemctl start ollama

# Verificar que el servicio está activo
systemctl status ollama

# Verificar que la API responde
curl http://localhost:11434/api/version
```

---

## 4. Modelos Instalados

```bash
# Ver modelos disponibles localmente
ollama list

# Descargar modelos
ollama pull *(completar — ej. qwen2.5:7b, llama3.2:3b, mistral:7b)*
```

| Modelo | Tamaño aprox. | Uso |
|---|---|---|
| *(completar)* | *(completar)* | *(completar)* |

---

## 5. Estructura de Ficheros

```
/usr/local/bin/
└── ollama                   ← Binario principal

/etc/systemd/system/
└── ollama.service           ← Servicio systemd (generado por el instalador)

/root/.ollama/               ← (o /usr/share/ollama/.ollama/ según versión)
└── models/                  ← Modelos descargados
```

```bash
# Localizar dónde están los modelos
ollama list
find / -name "*.gguf" 2>/dev/null | head -5
```

---

## 6. Servicios

| Servicio | Puerto | Descripción |
|---|---|---|
| **ollama** | 11434 TCP | API REST para inferencia LLM |
| **openssh-server** | 22 TCP | Acceso administrativo |

---

## 7. Flujo de Uso

```
Servicios del homelab
        │
        │ HTTP POST → 192.168.1.XX:11434/api/generate
        ▼
CT srv-02-ct-llm (Ollama)
        │
        ▼
Modelo LLM local (sin salida a internet)
        │
        ▼
Respuesta JSON → servicio solicitante
```

> Ejemplo: `srv-01-ct-sudofeed` puede apuntar su `OLLAMA_HOST` a este CT en lugar de usar su Ollama local.

---

## 8. Configuración de Red (systemd-networkd)

```bash
# Ver configuración actual
cat /etc/systemd/network/*.network

# Verificar IP asignada
ip a show eth0
```

---

## 9. Exposición de la API en la Red

Por defecto Ollama escucha solo en `localhost`. Para que otros CTs puedan consumirlo:

```bash
# Editar el servicio para escuchar en todas las interfaces
systemctl edit ollama
```

Añadir en el fichero override:

```ini
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
```

```bash
systemctl daemon-reload
systemctl restart ollama

# Verificar que escucha en la red
ss -tlnp | grep 11434
```

---

## 10. Monitorización

> **Node Exporter no está instalado** — pendiente de configurar.

```bash
# Instalar Node Exporter
apt install -y prometheus-node-exporter
systemctl enable prometheus-node-exporter
systemctl start prometheus-node-exporter
```

Expone métricas en `http://192.168.1.XX:9100/metrics` para Grafana.

### Estado de Ollama

```bash
# Verificar que la API responde
curl http://localhost:11434/api/version

# Ver modelos cargados en memoria
curl http://localhost:11434/api/ps

# Uso de recursos durante inferencia
top
```

---

## 11. Comandos Útiles

```bash
# Estado del servicio
systemctl status ollama

# Logs en tiempo real
journalctl -u ollama -f

# Listar modelos disponibles
ollama list

# Descargar un modelo
ollama pull <modelo>

# Eliminar un modelo
ollama rm <modelo>

# Prueba rápida de inferencia por consola
ollama run <modelo> "Hola, ¿funcionas correctamente?"

# Prueba de la API REST
curl http://localhost:11434/api/generate -d '{
  "model": "<modelo>",
  "prompt": "Responde solo: OK",
  "stream": false
}'

# Ver cuánta RAM consume el modelo cargado
curl http://localhost:11434/api/ps

# Uso de disco de los modelos
du -sh ~/.ollama/models/ 2>/dev/null || du -sh /usr/share/ollama/.ollama/models/

# Reiniciar servicio
systemctl restart ollama
```

---

## 12. Lo que falta documentar / configurar

### Pendiente de completar en este documento
- **IP del CT** — no visible en la salida; completar en sección 1 y sección 9
- **ID del CT** — presumiblemente 198 (único CT conocido en srv-02)
- **Modelos instalados** — ejecutar `ollama list` y completar la tabla de la sección 4
- **Directorio de modelos** — varía según versión de Ollama; verificar con `find`

### Pendiente de configurar
- **Node Exporter** — no instalado; sin métricas del CT en Grafana
- **`OLLAMA_HOST=0.0.0.0`** — sin esto, la API solo responde en localhost y otros CTs no pueden consumirla
- **Límite de memoria** — sin configurar `OLLAMA_MAX_LOADED_MODELS` ni `OLLAMA_NUM_PARALLEL`; con RAM limitada puede ser necesario
- **UFW** — sin reglas de cortafuegos; cualquier CT de la red puede llamar a la API