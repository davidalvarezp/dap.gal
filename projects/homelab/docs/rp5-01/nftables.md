
# RP5-01 - nftables.conf

Contenido completo de nftables.conf

```bash
#!/usr/sbin/nft -f


#!---VARIABLES---!#
define INT_ETH = "br0"
define PORT_SSH = "22"
define PORT_STATS = "9100"

flush ruleset

table inet filter {
        chain input {
                type filter hook input priority 0;
                policy drop;

                # Loopback
                iifname "lo" accept

                # Con EST o REL
                ct state established,related accept

                # PING
                icmp type echo-request limit rate 5/second accept
                icmpv6 type { echo-request, nd-neighbor-solicit, nd-neighbor-advert, nd-router-solicit, nd-router-advert } accept

                # SSH
                tcp dport $PORT_SSH accept

                # STATS
                tcp dport $PORT_STATS accept

        }

        chain forward {
                type filter hook forward priority 0;
                policy accept;

                # Traf BRIDGE
                iifname $INT_ETH accept
                oifname $INT_ETH accept

        }

        chain output {
                type filter hook output priority 0;
                policy accept;
        }
}

```