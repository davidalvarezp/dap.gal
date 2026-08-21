    1  clear
    2  apt update 
    3  apt update && apt upgrade -y && apt install -y curl wget jq
    4  wget -q https://github.com/traefik/traefik/releases/download/v3.3.4/traefik_v3.3.4_linux_amd64.tar.gz -O /tmp/traefik.tar.gz
    5  tar -xzf /tmp/traefik.tar.gz -C /tmp
    6  install -m 755 /tmp/traefik /usr/local/bin/traefik
    7  rm -f /tmp/traefik.tar.gz /tmp/traefik
    8  traefik version
    9  useradd -r -s /usr/sbin/nologin traefik
   10  mkdir -p /etc/traefik/conf.d
   11  mkdir -p /var/log/traefik
   12  chown -R traefik:traefik /etc/traefik /var/log/traefik
   13  id traefik
   14  ls -la /etc/traefik/
   15  clear
   16  cat > /etc/traefik/traefik.yml << 'EOF'
log:
  level: INFO
  filePath: /var/log/traefik/traefik.log

accessLog:
  filePath: /var/log/traefik/access.log

api:
  dashboard: true
  insecure: true

entryPoints:
  web:
    address: ":8080"
    forwardedHeaders:
      trustedIPs:
        - "192.168.1.39"
  lan:
    address: ":80"
    forwardedHeaders:
      trustedIPs:
        - "192.168.1.0/24"
  ssh:
    address: ":2222"
  traefik:
    address: ":8888"

providers:
  file:
    directory: /etc/traefik/conf.d
    watch: true
EOF

   17  clear
   18  cat /etc/traefik/traefik.yml
   19  clear
   20  traefik --configFile=/etc/traefik/traefik.yml &
   21  sleep 3
   22  curl -s http://localhost:8888/api/overview | jq .
   23  clear
   24  kill %1
   25  sleep 1
   26  clear
   27  cat > /etc/traefik/conf.d/dap.gal.yml << 'EOF'
http:
  routers:
    dap-gal:
      entryPoints:
        - web
      rule: "Host(`dap.gal`) || Host(`www.dap.gal`)"
      service: svc-hosting

  services:
    svc-hosting:
      loadBalancer:
        servers:
          - url: "http://192.168.1.40:80"
EOF

   28  clear
   29  cat /etc/traefik/conf.d/dap.gal.yml
   30  clear
   31  cat > /etc/traefik/conf.d/lan.yml << 'EOF'
http:
  routers:
    dns:
      entryPoints:
        - lan
      rule: "Host(`dns.dap.gal`)"
      service: svc-dns
      middlewares:
        - redirect-admin

    proxy:
      entryPoints:
        - lan
      rule: "Host(`proxy.dap.gal`)"
      service: svc-proxy

    stats:
      entryPoints:
        - lan
      rule: "Host(`stats.dap.gal`)"
      service: svc-stats

    home:
      entryPoints:
        - lan
      rule: "Host(`home.dap.gal`)"
      service: svc-home

  services:
    svc-dns:
      loadBalancer:
        servers:
          - url: "http://192.168.1.20"

    svc-proxy:
      loadBalancer:
        servers:
          - url: "http://192.168.1.31:8888"

    svc-stats:
      loadBalancer:
        servers:
          - url: "http://192.168.1.32:3000"

    svc-home:
      loadBalancer:
        servers:
          - url: "http://192.168.1.33:80"

  middlewares:
    redirect-admin:
      redirectRegex:
        regex: "^http://dns\\.dap\\.gal/?$"
        replacement: "http://dns.dap.gal/admin/"
        permanent: false
EOF

   32  clear
   33  cat /etc/traefik/conf.d/lan.yml
   34  clear
   35  nano /etc/traefik/conf.d/lan.yml
   36  clear
   37  curl -s http://localhost:8888/api/http/routers | jq '.[].rule'
   38  traefik --configFile=/etc/traefik/traefik.yml &
   39  sleep 3
   40  curl -s http://localhost:8888/api/http/routers | jq '.[].rule'
   41  clear
   42  kill %1
   43  sleep 1
   44  cat > /etc/traefik/conf.d/dap.gal.yml << 'EOF'
http:
  routers:
    dap-gal:
      entryPoints:
        - web
      rule: "Host(`dap.gal`) || Host(`www.dap.gal`)"
      service: svc-hosting

  services:
    svc-hosting:
      loadBalancer:
        servers:
          - url: "http://192.168.1.40:80"
EOF

   45  traefik --configFile=/etc/traefik/traefik.yml &
   46  sleep 3
   47  curl -s http://localhost:8888/api/http/routers | jq '.[].rule'
   48  kill %1
   49  sleep 1
   50  cat > /etc/systemd/system/traefik.service << 'EOF'
[Unit]
Description=Traefik reverse proxy
After=network-online.target
Wants=network-online.target

[Service]
Type=notify
User=traefik
Group=traefik
ExecStart=/usr/local/bin/traefik --configFile=/etc/traefik/traefik.yml
Restart=on-failure
RestartSec=5s
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=/var/log/traefik

[Install]
WantedBy=multi-user.target
EOF

   51  systemctl daemon-reload
   52  systemctl enable traefik
   53  systemctl start traefik
   54  sleep 2
   55  systemctl status traefik
   56  clear
   57  # Permiso para abrir puertos bajos
   58  setcap 'cap_net_bind_service=+ep' /usr/local/bin/traefik
   59  # Corregir el servicio (Type=simple, no notify)
   60  cat > /etc/systemd/system/traefik.service << 'EOF'
[Unit]
Description=Traefik reverse proxy
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=traefik
Group=traefik
ExecStart=/usr/local/bin/traefik --configFile=/etc/traefik/traefik.yml
Restart=on-failure
RestartSec=5s
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=/var/log/traefik

[Install]
WantedBy=multi-user.target
EOF

   61  systemctl daemon-reload
   62  systemctl restart traefik
   63  sleep 2
   64  systemctl status traefik
   65  clear
   66  systemctl disable traefik 2>/dev/null
   67  systemctl stop traefik 2>/dev/null
   68  cat > /etc/systemd/system/traefik.service << 'EOF'
[Unit]
Description=Traefik
After=network.target

[Service]
ExecStart=/usr/local/bin/traefik --configFile=/etc/traefik/traefik.yml
Restart=always

[Install]
WantedBy=multi-user.target
EOF

   69  systemctl daemon-reload
   70  systemctl enable traefik
   71  systemctl start traefik
   72  sleep 2
   73  systemctl status traefik
   74  curl -s http://localhost:8888/api/http/routers | jq '.[].rule'
   75  clear
   76  nano /etc/traefik/conf.d/dap.gal.yml
   77  clear
   78  curl -s http://localhost:8888/api/http/routers | jq '.[].rule'
   79  clear
   80  sed -i 's|Host(`\[www.dap.gal\](https://www.dap.gal)`)|Host(`www.dap.gal`)|g' /etc/traefik/conf.d/dap.gal.yml
   81  cat /etc/traefik/conf.d/dap.gal.yml
   82  ufw disable 
   83  ss -tlnp | grep traefik
   84  clear
   85  mkdir -p /etc/traefik/env
   86  nano /etc/traefik/env/cloudflare.env
   87  clear
   88  chmod 600 /etc/traefik/env/cloudflare.env
   89  clear
   90  nano /etc/traefik/traefik.yml
   91  nano /etc/traefik/traefik.yml
   92  clear
   93  touch /etc/traefik/acme.json
   94  chmod 600 /etc/traefik/acme.json
   95  nano /etc/systemd/system/traefik.service
   96  systemctl daemon-reload
   97  systemctl restart traefik.service 
   98  clear
   99* nano /etc/systemd/system/traefik.servic
  100  nano /etc/traefik/traefik.yml
  101  nano /etc/traefik/traefik.yml
  102  ls /etc/traefik/conf.d/lan.yml 
  103  nano /etc/traefik/conf.d/lan.yml 
  104  systemctl restart traefik.service 
  105  clear
  106  nano /etc/traefik/conf.d/dap.gal.yml
  107  clear
  108  rm -f /etc/traefik/conf.d/lan.yml
  109  rm -f /etc/traefik/conf.d/ssh.yml
  110  systemctl restart traefik
  111  sleep 3
  112  systemctl status traefik
  113  clear
  114  ls -la
  115  history