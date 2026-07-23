# BM01-pi5 - nftables.conf

Contenido actualizado del archivo `/etc/nftables.conf`

```conf
#!/usr/sbin/nft -f

#!---VARIABLES---!#
define INT_ETH = "br0"
define PORT_SSH = "22"
define PORT_STATS = "9100"

flush ruleset

#!----REGLAS----!#
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
		# policy drop;,
                # permitimos para la VPN:
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