# MAMA CHOL VPN — Complete Setup Guide

## Prerequisites

- Ubuntu 22.04 LTS (Oracle Cloud Free Tier ARM recommended)
- 4 vCPU, 24 GB RAM (Oracle Free Tier)
- Domain name pointed to server IP
- Root or sudo access

---

## Step 1: Initial Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install essential tools
sudo apt install -y curl wget git ufw fail2ban

# Configure firewall
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 54321/tcp  # X-UI panel
sudo ufw enable

# Enable BBR congestion control
echo "net.core.default_qdisc=fq" >> /etc/sysctl.conf
echo "net.ipv4.tcp_congestion_control=bbr" >> /etc/sysctl.conf
sysctl -p
```

## Step 2: Install X-UI Panel

```bash
bash <(curl -Ls https://raw.githubusercontent.com/mhsanaei/3x-ui/master/install.sh)
```

Access at: `http://YOUR_IP:54321`
Default credentials: `admin / admin` — **Change immediately!**

## Step 3: Configure VPN Inbounds

In X-UI panel, add these inbounds:

### VLESS Reality (Port 443)
- Protocol: vless
- Port: 443
- Network: tcp
- Security: reality
- SNI: www.google.com (or any CDN domain)

### VMess WebSocket (Port 8080)
- Protocol: vmess
- Port: 8080
- Network: ws
- Path: /vpn

### Trojan gRPC (Port 8443)
- Protocol: trojan
- Port: 8443
- Network: grpc
- Service Name: vpn

### Shadowsocks (Port 8388)
- Protocol: shadowsocks
- Port: 8388
- Method: chacha20-ietf-poly1305

## Step 4: Install PostgreSQL & Redis

```bash
# PostgreSQL
sudo apt install -y postgresql postgresql-contrib
sudo -u postgres psql -c "CREATE DATABASE mamachol;"
sudo -u postgres psql -c "CREATE USER mamacholuser WITH PASSWORD 'strongpassword';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE mamachol TO mamacholuser;"

# Redis
sudo apt install -y redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

## Step 5: Install Python & Backend

```bash
sudo apt install -y python3.11 python3.11-venv python3-pip

cd /opt
git clone https://github.com/your-org/Mama-Chol.git
cd Mama-Chol

python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
nano .env  # Fill in all values
```

## Step 6: Install Nginx

```bash
sudo apt install -y nginx
sudo cp server-setup/configs/nginx.conf /etc/nginx/sites-available/mamachol
sudo ln -s /etc/nginx/sites-available/mamachol /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

## Step 7: SSL Certificate

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d mamachol.online -d www.mamachol.online
```

## Step 8: Start Backend Service

```bash
# Create systemd service
sudo nano /etc/systemd/system/mamachol.service
```

```ini
[Unit]
Description=MAMA CHOL VPN Backend
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/Mama-Chol
ExecStart=/opt/Mama-Chol/venv/bin/uvicorn backend.api.main:app --host 127.0.0.1 --port 8000
Restart=always
EnvironmentFile=/opt/Mama-Chol/.env

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable mamachol
sudo systemctl start mamachol
```

## Step 9: Verify Installation

```bash
curl http://localhost:8000/health
# Expected: {"status": "ok"}
```

---

## Oracle Cloud Free Tier Tips

- Use ARM-based Ampere A1 instances for best performance
- Enable IPv6 in VCN settings
- Open ports in Security List, not just UFW
- Use Object Storage for backups (always free)
