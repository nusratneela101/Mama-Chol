# MAMA CHOL VPN — Troubleshooting Guide

## Cannot Connect to VPN

### Check 1: Internet Connection
```bash
ping 8.8.8.8
curl -I https://google.com
```

### Check 2: Server Status
Visit our status page: https://status.mamachol.online

### Check 3: Port Blocked by ISP
Try different protocols:
- VLESS Reality (443) — looks like HTTPS
- VMess WS (8080) — alternative port
- Trojan gRPC (8443)

### Check 4: Firewall
```bash
# Check if port is reachable
nc -zv YOUR_SERVER_IP 443
telnet YOUR_SERVER_IP 443
```

### Check 5: Config Validity
Regenerate your config from Dashboard → My Config → Regenerate

---

## Slow VPN Speed

**Step 1:** Run speed test without VPN, then with VPN.
```
Without VPN: 100Mbps down / 50Mbps up
With VPN: should be 70-90% of original
```

**Step 2:** Switch protocols
VLESS Reality > Trojan gRPC > VMess WS > Shadowsocks

**Step 3:** Change server region
Pick server closest to you geographically.

**Step 4:** Check server load
In dashboard, avoid servers showing >80% load.

**Step 5:** Enable BBR on server
```bash
sudo sysctl net.ipv4.tcp_congestion_control
# Should show: bbr
```

---

## Payment Issues

### Payment Deducted but Plan Not Activated
1. Wait 5-10 minutes (payment processing)
2. Check email for confirmation
3. If not resolved, go to Dashboard → Support
4. Provide: transaction ID, payment method, amount, time

### bKash Payment Failing
- Ensure bKash account has sufficient balance
- Use Mobile Menu → Payment → Pay Bill (not Send Money)
- Merchant number: **01XXXXXXXXX**
- Reference: your registered email

### Nagad Payment Failing
- Enable mobile data (not WiFi) for Nagad
- Update Nagad app to latest version

---

## Installation Issues

### Python dependencies fail
```bash
sudo apt install -y python3.11-dev libpq-dev build-essential
pip install -r requirements.txt
```

### PostgreSQL connection refused
```bash
sudo systemctl status postgresql
sudo -u postgres psql -c "\l"
# Check DATABASE_URL in .env
```

### Redis connection refused
```bash
sudo systemctl status redis
redis-cli ping
# Should return: PONG
```

### Nginx not serving SSL
```bash
sudo certbot renew --dry-run
sudo nginx -t
sudo systemctl reload nginx
```

---

## X-UI Panel Issues

### Cannot access X-UI panel
```bash
sudo systemctl status x-ui
# If stopped:
sudo systemctl start x-ui

# Check logs:
sudo journalctl -u x-ui -f
```

### Inbound not working
1. Open X-UI panel
2. Go to Inbounds
3. Click the inbound → check if enabled (green toggle)
4. Click the traffic icon to reset stats
5. Restart X-UI: `sudo systemctl restart x-ui`

---

## AI Chatbot Not Responding

```bash
# Check Ollama service
systemctl status ollama
curl http://localhost:11434/api/tags

# If model not found, pull it:
ollama pull mistral
```

---

## Database Migration Issues

```bash
cd /opt/Mama-Chol
source venv/bin/activate
alembic upgrade head
# If error, check DATABASE_URL in .env
```

---

## Getting Help

1. **AI Chat:** Available 24/7 on our website
2. **Telegram:** @mamacholsupport
3. **Email:** support@mamachol.online
4. **Dashboard Ticket:** Fastest response time

**When contacting support, include:**
- Your email/username
- Error message (screenshot)
- Operating system and VPN client
- Payment transaction ID (for payment issues)
