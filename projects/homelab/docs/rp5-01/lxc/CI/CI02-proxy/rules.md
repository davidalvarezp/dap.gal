# CI02-proxy

Contenido del archivo `/etc/traefik/conf.d/rules.yml`

```conf
http:
  routers:
    # Infraestructura (Subdominios)
    dns:
      rule: "Host(`dns.dap.gal`)"
      service: srv-dns
      entryPoints: [websecure]
      tls: { certResolver: cloudflare }

    proxy:
      rule: "Host(`proxy.dap.gal`)"
      service: srv-proxy
      entryPoints: [websecure]
      tls: { certResolver: cloudflare }

    home:
      rule: "Host(`home.dap.gal`)"
      service: srv-home
      entryPoints: [websecure]
      tls: { certResolver: cloudflare }

    # Públicos (Paths)
    web:
      rule: "Host(`dap.gal`) && Path(`/`)"
      service: srv-web
      entryPoints: [websecure]
      tls: { certResolver: cloudflare }
    blog:
      rule: "Host(`dap.gal`) && Path(`/blog`)"
      service: srv-blog
      entryPoints: [websecure]
      tls: { certResolver: cloudflare }

  services:
    srv-dns:
      loadBalancer:
        servers: [{ url: "http://192.168.1.11/admin" }]
    srv-proxy:
      loadBalancer:
        servers: [{ url: "http://192.168.1.12" }]
    srv-home:
      loadBalancer:
        servers: [{ url: "http://192.168.1.15:3000" }]
    srv-web:
      loadBalancer:
        servers: [{ url: "http://192.168.1.31" }]
    srv-blog:
      loadBalancer:
        servers: [{ url: "http://192.168.1.32" }]
```
