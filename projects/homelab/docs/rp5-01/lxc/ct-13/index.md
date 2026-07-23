# ct-13 - Contenedor Base Debian 13 (Trixie)

## 1. Instalación y Primer Acceso

Para crear el contenedor:

```bash
sudo lxc-create -n ct-13 -t download -- -d debian -r trixie -a arm64
sudo lxc-start -n ct-13
sudo lxc-attach -n ct-13
```

---

## 2. Herramientas Esenciales

Lo primero es mejorar el uso de la terminal. Instalaremos actualizaciones de seguridad automáticas, herramientas básicas y autocompletado.

```bash
apt update && apt upgrade -y
apt install -y sudo curl wget vim nano htop net-tools dnsutils \
bash-completion git ufw unattended-upgrades apt-listchanges
```


### Activar Autocompletado

Edita el archivo `/etc/bash.bashrc` para asegurar que el autocompletado funcione para todos los usuarios:

```bash
# Descomenta estas líneas si no lo están
if ! shopt -oq posix; then
  if [ -f /usr/share/bash-completion/bash_completion ]; then
    . /usr/share/bash-completion/bash_completion
  elif [ -f /etc/bash_completion ]; then
    . /etc/bash_completion
  fi
fi
```

### Generar LOCALE

```bash
locale-gen en_US.UTF-8
update-locale LANG=en_US.UTF-8
export LANG=en_US.UTF-8
```

---

## 3. Firewall

Como en el host utilicé nftables, en los contenedores utilizaré UFW, permitiendo únicamente lo necesario y bloqueando todo lo demás por defecto.

> **Nota:** Si permites una regla, pero aún así se bloquea, revisa que no la bloquee el host (nftables).

```bash
# Establecer políticas por defecto
ufw default deny incoming
ufw default allow outgoing

# OPCIONAL: Permitir SSH para acceder a los contenedores en remoto.
ufw allow ssh

# Habilitar el firewall
ufw enable
```
*En cada clon, solo añadir el puerto específico, por ejemplo: `ufw allow 80/tcp` para Nginx (HTTP).*

---

## 4. Actualizaciones Automáticas

Ahora que el contenedor se mantenga seguro instalando automáticamente los parches de seguridad.

Configura el paquete:
```bash
dpkg-reconfigure -plow unattended-upgrades
# (Selecciona "Sí" en la pantalla azul).
```

Verifica que esté activo:

```bash
systemctl status unattended-upgrades
```

---

## 5. Monitorización (Prometheus + Grafana)
Para que Prometheus recoja los datos, necesitamos exportar las métricas del contenedor.

**Node Exporter** es el estándar para métricas de hardware (CPU, RAM, etc).

```bash
apt install -y prometheus-node-exporter
systemctl enable prometheus-node-exporter

# Abrimos el puerto para que el contenedor de stats pueda leer los datos
ufw allow 9100/tcp
```

---

## 6. Configuración de Usuario

Nunca es una buena práctica hacer todo como `root`. Crea un usuario estándar para las demos:

```bash
adduser davidalvarezp
usermod -aG sudo davidalvarezp
su - davidalvarezp
```

---

## 7. Configuración de red

Deshabilitar DHCP, así cuando se defina la IP estática el contenedor, no tendrá 2 IPs (Estática+DHCP).

Editamos en el archivo de configuración `/etc/systemd/network/eth0.network`:
```conf
[Match]
Name=eth0
#
[Network]
DHCP=no
```
Reiniciamos y limpiamos:

```bash
systemctl restart systemd-networkd
ip addr flush dev eth0
```

---

## 8. Limpieza Pre-Clonación
Para que los clones no hereden basura o IDs de red idénticos:

```bash
# Limpiar caché de paquetes
apt clean
apt autoremove

# Limpiar el historial de comandos
history -c && exit
```

---
## 9. Crear plantilla

Sal del contenedor, detener y clonar:

```bash
sudo lxc-stop -n ct-13

# Comando para clonar el contenedor:
sudo lxc-copy -n ct-13 -N Contenedor-Nuevo
```

---
## 10. Configuración del clon

Para establecer una IP estática y limitar los recursos:

1. En el **host**, localiza el archivo de configuración (/var/lib/lxc/$NOMBRE/config)
2. Copia los bloques a utilizar partiendo del archivo [config](../../config.md).
3. Cambia los valores adaptándolos a los recursos de tu sistema.
---

## Resumen
| Característica | Herramienta | Resultado |
| :--- | :--- | :--- |
| **Firewall** | UFW | Seguridad robusta y sencilla |
| **Updates** | Unattended-upgrades | No necesita mantenimiento |
| **Terminal** | Bash-completion | Ayuda al escribir comandos |
| **Red** | IP estática | Configurada /var/lib/lxc/*/config |
| **Métricas** | Node-Exporter | Envía datos al contenedor Stats |
