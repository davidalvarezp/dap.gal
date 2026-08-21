    1  clear
    2  apt update && apt install -y nginx
    3  systemctl enable nginx
    4  systemctl start nginx
    5  systemctl status nginx
    6  clear
    7  ufw disable 
    8  apt install openssh-server 
    9  clear
   10  useradd -m -s /bin/bash dap
   11  mkdir -p /home/dap/.ssh
   12  chmod 700 /home/dap/.ssh/
   13  clear
   14  mkdir -p /var/www/dap.gal
   15  chown -R dap:www-data /var/www/dap.gal
   16  chmod -R 755 /var/www/dap.gal
   17  clear
   18  nano /etc/nginx/sites-available/dap.gal
   19  ln -s /etc/nginx/sites-available/dap.gal /etc/nginx/sites-enabled/
   20  rm -f /etc/nginx/sites-enabled/default
   21  nginx -t && systemctl reload nginx
   22  clear
   23  apt install nginx
   24  clear
   25  systemctl status nginx.service 
   26  clear
   27  passwd dap
   28  nano /etc/ssh/sshd_config
   29  systemctl restart ssh
   30  systemctl restart sshd
   31  clear
   32  ls /var/www/dap.gal/
   33  ls -la /var/www/dap.gal/
   34  apt install tree
   35  clear
   36  tree
   37  cd /var/www/dap.gal/
   38  clear
   39  tree
   40  clear
   41  nano /etc/nginx/sites-available/dap.gal
   42  nginx -t && systemctl reload nginx
   43  clear
   44  chown -R dap:www-data /var/www/dap.gal
   45  find /var/www/dap.gal -type d -exec chmod 755 {} \;
   46  find /var/www/dap.gal -type f -exec chmod 644 {} \;
   47  clear
   48  chown -R dap:www-data /var/www/dap.gal
   49  find /var/www/dap.gal -type f -exec chmod 644 {} \;
   50  find /var/www/dap.gal -type d -exec chmod 755 {} \;
   51  history