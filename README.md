# vpnfarm
Python Script to manage a farm of docker instances from an openvpn server


IMPORTANT:

Due to the issues (both technically and philosophally) related to automatically configuring iptables, I decided to use fix IPs in openvpn instead.

The start and stop of both server and client are done using simple shell scripts.
