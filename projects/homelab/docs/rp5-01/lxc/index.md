# Linux Containers

## Instalación y configuración

```bash
sudo systemctl enable lxc.service 
sudo systemctl stop lxc-net.service 
sudo systemctl disable lxc-net.service
sudo nano /etc/default/lxc-net      # Ver Archivos
sudo nano /etc/lxc/default.conf     # Ver Archivos
sudo systemctl restart lxc.service 
```

---

## Contenedores

### Crear 

```bash
# Importar contenedor:
sudo lxc-create -n $NOMBRE -t $PLANTILLA -- -d $DISTRIBUCION -r $VERSION -a $ARQUITECTURA

# Para debian 12:
sudo lxc-create -n ct-13 -t download -- -d debian -r trixie -a arm64
```

### Listar

```bash
sudo lxc-ls -f
```

### Iniciar/Parar 

```bash
sudo lxc-start $NOMBRE
sudo lxc-stop $NOMBRE
```

## Archivos
### [/etc/default/lxc-net](lxc-net.md) 
### /etc/lxc/default.conf 