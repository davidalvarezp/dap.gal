# BM01-pi5

Esta guía detalla la instalación y configuración del BareMetal 01, la Raspberry Pi 5 de 8GB RAM y 128GB SSD.

## Configuracón del sistema

```bash
sudo apt update
sudo apt full-upgrade -y
sudo rpi-eeprom-update -a


sudo systemctl enable fstrim.timer
sudo systemctl start fstrim.timer
lsblk --discard 
lsblk -l

sudo apt install lxc lxc-templates bridge-utils -y
sudo systemctl enable lxc.service
lxc-checkconfig

sudo apt install zram-tools -y
sudo apt install nftables -y


echo "net.ipv4.ip_forward=1" | sudo tee /etc/sysctl.d/99-ipforward.conf
sudo sysctl -p /etc/sysctl.d/99-ipforward.conf

sudo systemctl enable nftables.service 
sudo systemctl start nftables.service

sudo nano /etc/nftables.conf # Sustituye por el nftables.conf de este directorio

sudo systemctl restart nftables.service

sudo apt install fail2ban -y
```

## Configuración de red

```bash
sudo nmcli connection delete eth0 2>/dev/null

sudo nmcli connection add type bridge ifname br0 con-name br0
sudo nmcli connection modify br0 ipv4.addresses 192.168.1.100/24
sudo nmcli connection modify br0 ipv4.gateway 192.168.1.1
sudo nmcli connection modify br0 ipv4.gateway 192.168.1.1
sudo nmcli connection modify br0 ipv4.dns "8.8.8.8,1.1.1.1"
sudo nmcli connection modify br0 ipv4.method manual
sudo nmcli connection add type ethernet ifname eth0 master br0 con-name br-eth0
sudo nmcli connection up br0
```


## Monitorizacion

```bash

#Prometheus (para grafana)
sudo apt install prometheus-node-exporter



#Glances (para Homepage)
sudo apt install python3

root@raspberrypi:~# cd ~
python3 -m venv ~/.venv
source ~/.venv/bin/activate
pip install glances



sudo nano /boot/firmware/cmdline.txt
    # -> Añade al final: cgroup_enable=cpuset cgroup_enable=memory cgroup_memory=1
sudo reboot
```