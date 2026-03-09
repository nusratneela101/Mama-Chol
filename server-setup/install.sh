#!/bin/bash
# MAMA CHOL VPN - Server Installation Script
# Tested on Ubuntu 22.04 LTS
set -e

echo "=== MAMA CHOL VPN - Server Setup ==="

# System update
apt update && apt upgrade -y
apt install -y curl wget git ufw certbot python3-certbot-nginx nginx haproxy

# Enable BBR (performance optimization for China)
modprobe tcp_bbr
echo "tcp_bbr" >> /etc/modules-load.d/modules.conf
echo "net.core.default_qdisc=fq" >> /etc/sysctl.conf
echo "net.ipv4.tcp_congestion_control=bbr" >> /etc/sysctl.conf
sysctl -p

# Firewall
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 54321/tcp
ufw --force enable

# Install X-UI panel
bash <(curl -Ls https://raw.githubusercontent.com/alireza0/x-ui/master/install.sh) <<< "$(printf 'admin\nadmin\n54321\n')"

# SSL certificate
read -p "Enter your domain (e.g. mamachol.online): " DOMAIN
certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m admin@"$DOMAIN"

echo "=== Installation Complete ==="
echo "X-UI Panel: http://$(curl -s ifconfig.me):54321"
