# CS Home: Homepage

Ahora empieza la parte divertida: **darle una cara visual a tu Homelab**.

**Homepage** es perfecto para esto. Es un panel estático, rápido y muy estético que se conecta vía API a tus otros contenedores para mostrarte el estado de tu CPU, cuántos anuncios ha bloqueado Pi-hole o si Kuma detecta algún fallo.

---

## 1. Despliegue del Contenedor
Como es una aplicación que corre sobre **Node.js**, vamos a clonar nuestra base Debian y prepararla.

Desde el host (Raspberry Pi):
```bash
# Clonar
sudo lxc-copy -n B0-deb12 -N CI05-home

# Copia el contenido de config.conf
sudo nano /var/lib/lxc/CI05-home/config

# Iniciar y entrar
sudo lxc-start -n CI05-home
sudo lxc-attach -n CI05-home

# Configurar DNS 
rm /etc/resolv.conf
echo "nameserver 192.168.1.101" > /etc/resolv.conf
echo "nameserver 8.8.8.8" >> /etc/resolv.conf
```

---

## 2. Instalación de Homepage 

### 1. Instalación de Node.js (El motor)

Homepage requiere Node.js 18 o superior. Usaremos el repositorio oficial de NodeSource para tener una versión estable y moderna en tu Debian 12.

Dentro de **CI05-home**:
```bash
# Instalamos dependencias previas
apt update && apt install -y curl git sudo

# Descargamos e instalamos el script de NodeSource (Node 20 LTS)
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs
```

Verifica la versión: `node -v` (debería salir v20.x.x).

---

## 2. Descarga y Preparación de Homepage

Vamos a colocar la aplicación en `/opt/homepage`:

```bash
cd /opt
git clone https://github.com/gethomepage/homepage.git
cd homepage

# Instalar las dependencias de la aplicación
npm install -g pnpm
pnpm install

pnpm approve-builds
# Seleciona a (todos)
# Do you approve? (y/N) · true
# Selecciona y

# Compilar la aplicación para producción (esto puede tardar 1-2 min en la Pi 5)
pnpm build
#npm run build

ufw allow 3000/tcp
```

---

## 3. Configuración Inicial

Homepage busca sus archivos en una carpeta llamada `config`. Vamos a crear una configuración básica.

```bash
# Si no existe, creamos la carpeta de configuración
mkdir -p config
```

Modfica el archivo de servicios: `nano config/services.yaml`

Copiar el archivo services.yml

Modifica el archivo de widgets: `nano config/widgets.yaml`

Copiar el archivo widgets.yml

---

## 4. Crear el Servicio de Sistema (Persistence)

Necesitamos que `systemd` se encargue de arrancar Homepage automáticamente si el contenedor se reinicia.

Crea el archivo del servicio:
```bash
sudo nano /etc/systemd/system/homepage.service`
# Copia el contenido de homepage
```

**Activa el servicio:**
```bash
systemctl daemon-reload
systemctl enable homepage
systemctl start homepage
```

---

## 5. Acceso y Verificación
Homepage corre por defecto en el puerto **3000**.

1. Abre tu navegador y ve a: `http://192.168.1.105:3000`
2. ¡Deberías ver tu dashboard con los botones de Pi-hole y Proxy!

