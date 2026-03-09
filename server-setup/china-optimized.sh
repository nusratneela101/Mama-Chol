#!/bin/bash
# China-Optimized VPN Setup - VLESS+TLS+WebSocket
set -e
echo "=== China-Optimized Setup ==="
# Requires domain proxied through Cloudflare CDN
# Protocol: VLESS + TLS + WebSocket on port 443
# This disguises VPN traffic as normal HTTPS traffic

DOMAIN=${1:-"mamachol.online"}
UUID=$(cat /proc/sys/kernel/random/uuid)
echo "Generated UUID: $UUID"
echo "Add this to X-UI inbound config and configs/x-ui-config.json"
echo "Cloudflare: Enable proxy (orange cloud) for your domain"
echo "Set SSL/TLS mode to Full in Cloudflare"
