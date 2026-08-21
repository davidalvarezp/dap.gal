# CT rp5-01-ct-ssh: SSH Bastion

Contenedor dedicado a proporcionar acceso remoto seguro al homelab mediante **SSH con autenticación de dos factores (2FA)**. Actúa como único punto de entrada SSH desde internet, aislando el resto de servicios del acceso directo exterior. Usa **Google Authenticator (TOTP)** como segundo factor junto a contraseña.

---

## 1. Despliegue del Contenedor

En el nodo **Raspberry Pi 5** (`rp5-01`), creamos el contenedor Debian 12:

- **CPU** 1 socket
- **RAM** 256 MB
- **Disco** 4 GB
- **Red** 192.168.1.21

---

## 2. Preparación del Sistema

```bash
# Actualización base
apt update && apt upgrade -y
apt install -y curl bash-completion fail2ban

echo "source /etc/bash_completion" >> ~/.bashrc
source ~/.bashrc

# IP estática via systemd-networkd
cat > /etc/systemd/network/eth0.network << 'EOF'
[Match]
Name=eth0

[Network]
DHCP=no
Address=192.168.1.21/24
Gateway=192.168.1.1
DNS=192.168.1.20
EOF

systemctl enable systemd-networkd
systemctl restart systemd-networkd

ping -c 2 8.8.8.8
```

---

## 3. Instalación de Dependencias

```bash
# Servidor SSH + módulo PAM para 2FA
apt install -y openssh-server libpam-google-authenticator

# Métricas del sistema
apt install -y prometheus-node-exporter
systemctl enable prometheus-node-exporter
systemctl start prometheus-node-exporter
```

---

## 4. Estructura de Ficheros

```
/etc/ssh/
├── sshd_config              ← Configuración principal del servidor SSH
└── sshd_config.d/
    └── bastion.conf         ← Ajustes específicos del bastión

/etc/pam.d/
└── sshd                     ← Configuración PAM (contraseña + TOTP)

/etc/fail2ban/
├── jail.local               ← Reglas de bloqueo por intentos fallidos
└── filter.d/
    └── sshd.conf            ← Filtro de log para SSH

/home/<usuario>/
└── .google_authenticator    ← Secreto TOTP por usuario (chmod 400)
```

---

## 5. Servicios y Cuentas

| Servicio | Puerto | Descripción |
|---|---|---|
| **openssh-server** | 22 TCP | Servidor SSH (bastión) |
| **fail2ban** | — | Bloqueo automático por fuerza bruta |
| **prometheus-node-exporter** | 9100 TCP | Métricas del sistema para Grafana |

| Usuario | Acceso | Descripción |
|---|---|---|
| `root` | Deshabilitado | No permite login directo |
| `bastion` | Contraseña + TOTP | Usuario de acceso remoto |

---

## 6. Flujo de Acceso

```
Administrador (internet)
        │
        │ SSH → router:22 (NAT) → 192.168.1.21:22
        ▼
CT rp5-01-ct-ssh (bastión)
        │
   1. Contraseña
   2. Código TOTP (Google Authenticator)
        │
        │ Acceso concedido
        ▼
SSH interno hacia otros CTs de la red
        │
        ├── ssh usuario@192.168.1.31   (proxy)
        ├── ssh usuario@192.168.1.40   (whost)
        └── ssh usuario@192.168.1.XX   (resto)
```

> El router debe reenviar el puerto 22 (o un puerto externo no estándar) a `192.168.1.21:22`.

---

## 7. Configuración SSH

### `/etc/ssh/sshd_config`

```
# Protocolo y puerto
Port 22
Protocol 2

# Autenticación
PermitRootLogin no
MaxAuthTries 3
LoginGraceTime 30

# Método de autenticación: contraseña + PAM (2FA)
PasswordAuthentication yes
ChallengeResponseAuthentication yes
UsePAM yes
AuthenticationMethods keyboard-interactive

# Desactivar métodos no usados
PubkeyAuthentication no
PermitEmptyPasswords no
KerberosAuthentication no
GSSAPIAuthentication no

# Restricciones de acceso
AllowUsers bastion
MaxSessions 3

# Keepalive
ClientAliveInterval 120
ClientAliveCountMax 2

# Logging
LogLevel VERBOSE
SyslogFacility AUTH

# Deshabilitar forwarding innecesario
X11Forwarding no
AllowTcpForwarding yes    # necesario para saltar a otros CTs
AllowAgentForwarding no
PermitTunnel no
```

```bash
# Verificar sintaxis y reiniciar
sshd -t && systemctl restart ssh
```

---

## 8. Configuración 2FA (Google Authenticator / TOTP)

### Configurar PAM

Editar `/etc/pam.d/sshd`, añadir al principio del fichero:

```
# 2FA TOTP (antes de la autenticación de contraseña)
auth required pam_google_authenticator.so nullok

# Contraseña del sistema
@include common-auth
```

Comentar o eliminar la línea `@include common-password` si aparece duplicada.

### Generar el secreto TOTP por usuario

Ejecutar como cada usuario que necesite acceso:

```bash
# Como usuario bastion
su - bastion
google-authenticator
```

Responder a las preguntas del asistente:

```
Do you want authentication tokens to be time-based? → y
Do you want me to update your "~/.google_authenticator" file? → y
Do you want to disallow multiple uses of the same token? → y
By default, tokens are good for 30 seconds [...] Do you want to enable rate-limiting? → y
```

El asistente muestra:
- **QR Code** → escanear con Google Authenticator, Aegis, o similar
- **Secret key** → guardar en lugar seguro (KeePass, Bitwarden…)
- **Emergency scratch codes** → guardar en lugar seguro

```bash
# Asegurar permisos del fichero de secreto
chmod 400 /home/bastion/.google_authenticator
```

---

## 9. Creación del Usuario Bastión

```bash
# Crear usuario sin sudo
useradd -m -s /bin/bash bastion
passwd bastion

# Opcional: permitir saltar a otros CTs con su propia clave
mkdir -p /home/bastion/.ssh
chmod 700 /home/bastion/.ssh
chown bastion:bastion /home/bastion/.ssh
```

---

## 10. Fail2ban

### `/etc/fail2ban/jail.local`

```ini
[DEFAULT]
bantime  = 1h
findtime = 10m
maxretry = 5
ignoreip = 127.0.0.1/8 192.168.1.0/24

[sshd]
enabled  = true
port     = ssh
logpath  = /var/log/auth.log
maxretry = 3
bantime  = 24h
```

```bash
systemctl enable fail2ban
systemctl start fail2ban
```

---

## 11. Cortafuegos (UFW)

```bash
ufw default deny incoming
ufw default deny outgoing

# SSH entrante desde internet
ufw allow in 22/tcp

# DNS
ufw allow out 53/udp
ufw allow out 53/tcp

# NTP
ufw allow out 123/udp

# SSH saliente hacia la red interna (saltar a otros CTs)
ufw allow out to 192.168.1.0/24 port 22 proto tcp

# Node Exporter (métricas hacia Prometheus)
ufw allow in from 192.168.1.32 to any port 9100 proto tcp

ufw --force enable
ufw status verbose
```

| Dirección | Puerto | Origen / Destino | Motivo |
|---|---|---|---|
| IN | 22 | cualquiera | SSH externo |
| OUT | 53 | cualquiera | DNS |
| OUT | 123 | cualquiera | NTP |
| OUT | 22 | 192.168.1.0/24 | Salto a CTs internos |
| IN | 9100 | 192.168.1.32 (Prometheus) | Métricas |

---

## 12. Comandos Útiles

```bash
# Estado del servidor SSH
systemctl status ssh

# Ver intentos de login (éxitos y fallos)
journalctl -u ssh -f
grep "Accepted\|Failed" /var/log/auth.log

# IPs baneadas por fail2ban
fail2ban-client status sshd

# Desbanear una IP manualmente
fail2ban-client set sshd unbanip <IP>

# Verificar configuración SSH sin reiniciar
sshd -t

# Ver conexiones SSH activas
ss -tnp | grep :22
who

# Estado Node Exporter
systemctl status prometheus-node-exporter
curl -s http://localhost:9100/metrics | grep node_load
```

---

## 13. Acceso desde el Exterior

### Conexión al bastión

```bash
ssh bastion@<IP-publica-o-DDNS>
# 1. Solicita contraseña
# 2. Solicita código TOTP (6 dígitos de la app)
```

### Saltar a otros CTs desde el bastión

```bash
# Desde dentro del bastión
ssh usuario@192.168.1.31   # proxy
ssh usuario@192.168.1.40   # whost
ssh root@192.168.1.20      # dns
```

### SSH Jump (acceso directo en un paso desde el cliente)

```bash
ssh -J bastion@<IP-publica> usuario@192.168.1.31
```

Configuración en `~/.ssh/config` del cliente:

```
Host bastion
    HostName <IP-publica-o-DDNS>
    User bastion
    Port 22

Host proxy
    HostName 192.168.1.31
    User usuario
    ProxyJump bastion

Host whost
    HostName 192.168.1.40
    User dap
    ProxyJump bastion
```

---

## 14. Monitorización

Node Exporter expone métricas en `http://192.168.1.21:9100/metrics`.  
Prometheus las recoge automáticamente y Grafana las visualiza en el dashboard del homelab.

```bash
# Últimas líneas del log de autenticación
tail -20 /var/log/auth.log

# Resumen de intentos fallidos
grep "Failed password" /var/log/auth.log | awk '{print $11}' | sort | uniq -c | sort -rn | head -10

# Estado de fail2ban
fail2ban-client status sshd
```