# CI Estadísticas: Grafana

## 1. Despliegue del Contenedor
Desde el host:

```bash
sudo lxc-copy -n CB01-deb12 -N CI03-STATS

# Editar config
sudo nano /var/lib/lxc/CI03-STATS/config 

# Iniciar
sudo lxc-start -n CI03-STATS
sudo lxc-attach -n CI03-STATS

# Configuramos DNS
rm /etc/resolv.conf
echo "nameserver 192.168.1.11" > /etc/resolv.conf
echo "nameserver 8.8.8.8" >> /etc/resolv.conf

```

### 2. Instalación de Prometheus y Grafana

#### Instalar Prometheus

En Debian 12, el paquete suele llamarse prometheus. Si no lo encuentra, asegúrate de tener los componentes `main`:

```bash
apt update
apt install -y prometheus prometheus-node-exporter
```

Si esto falla, es que tu sources.list está muy limitado, pero con el comando anterior debería bastar.

#### Instalar Grafana (Repositorio Oficial)

Grafana no está en los repositorios de Debian por defecto. Tienes que añadir el suyo:

```bash
# 1. Instalar dependencias
apt install -y gnupg2 curl software-properties-common

# 2. Añadir la clave de Grafana
mkdir -p /etc/apt/keyrings/
curl https://apt.grafana.com/gpg.key | gpg --dearmor | tee /etc/apt/keyrings/grafana.gpg > /dev/null

# 3. Añadir el repositorio
echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com stable main" | tee /etc/apt/sources.list.d/grafana.list

# 4. Actualizar e instalar
apt update
apt install -y grafana
```

#### Arrancar los servicios

Una vez instalados, hay que activarlos para que inicien siempre con el contenedor:

```bash
# Prometheus
systemctl enable prometheus
systemctl start prometheus

# Grafana
systemctl enable grafana-server
systemctl start grafana-server
```

### 3. Configuración de Prometheus (El Recolector)
Debes decirle a Prometheus dónde están tus otros contenedores para que "lea" sus métricas.
Edita el archivo: `nano /etc/prometheus/prometheus.yml`

Añade tus contenedores en la sección `scrape_configs` (sustituye las IPs por las tuyas):

```yaml
scrape_configs:
  - job_name: 'homelab-nodes'
    static_configs:
      - targets: ['192.168.1.101:9100'] # Pi-hole
      - targets: ['192.168.1.104:9100'] # Nginx Proxy
      - targets: ['localhost:9100']      # Este mismo contenedor
```

*Reicia el servicio:* `systemctl restart prometheus`

### 4. Firewall (UFW)
Grafana usa el puerto **3000**. Prometheus usa el **9090**.

```bash
ufw allow 3000/tcp
ufw allow 9090/tcp
ufw reload
```

---

### 5. Configuración de Grafana (El Panel)

Habilita y arranca Grafana:

```bash
systemctl enable grafana-server
systemctl start grafana-server
```

Entra desde tu navegador a: `http://192.168.1.13:3000`
    * **User:** admin / **Pass:** admin (te pedirá cambiarla).

#### Conectar Grafana con Prometheus:
1.  Ve a **Connections** -> **Data Sources**.
2.  Click en **Add data source** y selecciona **Prometheus**.
3.  En URL pon: `http://localhost:9090`.
4.  Click en **Save & Test**.

---

### 6. El Toque Maestro para YouTube: Importar Dashboard
No pierdas tiempo creando gráficas de primeras. Usa el dashboard standar para Node Exporter:

1.  En Grafana, ve al icono de **"+" (arriba a la derecha)** -> **Import dashboard**.
2.  En "Import via grafana.com", escribe el ID: `1860`.
3.  Haz click en **Load**.
4.  Selecciona tu fuente de datos "Prometheus" y dale a **Import**.



---

### Arquitectura de Datos

1.  **Exportador (Node Exporter):** Instalado en cada LXC, extrae los datos del sistema.
2.  **Recolector (Prometheus):** Viaja por la red local cada X segundos "robando" esos datos.
3.  **Visualizador (Grafana):** Consulta a Prometheus y lo transforma en gráficas bonitas.
