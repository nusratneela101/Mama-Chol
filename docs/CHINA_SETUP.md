# MAMA CHOL VPN — China Setup Guide (中国设置指南)

This guide covers optimizing MAMA CHOL VPN specifically for users inside mainland China.

---

## Recommended Protocols for China

### 1. VLESS Reality (Best Choice)
VLESS Reality is currently the most effective protocol for bypassing the Great Firewall.

**Why it works:**
- Mimics TLS traffic of legitimate websites
- Uses real TLS certificates (no self-signed)
- Extremely difficult for DPI to detect
- No pattern matching possible

**Setup:**
```json
{
  "protocol": "vless",
  "settings": {
    "clients": [{"id": "your-uuid", "flow": "xtls-rprx-vision"}]
  },
  "streamSettings": {
    "network": "tcp",
    "security": "reality",
    "realitySettings": {
      "dest": "www.google.com:443",
      "serverNames": ["www.google.com"],
      "privateKey": "auto-generated",
      "shortIds": ["auto-generated"]
    }
  }
}
```

### 2. Trojan over gRPC
Good fallback when Reality is blocked.

### 3. VMess + WebSocket + TLS + CDN
Routes through Cloudflare CDN — virtually impossible to block.

---

## Server Location Recommendations

For China users, use servers in:
1. 🇯🇵 **Japan** (Tokyo) — Lowest latency ~50ms
2. 🇸🇬 **Singapore** — ~80ms, good speeds
3. 🇰🇷 **South Korea** — ~60ms
4. 🇺🇸 **USA West Coast** — ~180ms (for US content)

Avoid: Hong Kong (increasingly monitored), Taiwan

---

## Client Configuration

### Android: v2rayNG
1. Download from [GitHub Releases](https://github.com/2dust/v2rayNG/releases) (not Play Store in China)
2. Use VPN mode, not Proxy mode
3. Enable **Domain Strategy: UseIPv4**
4. Routing: Select **Bypass China** preset

### iOS: Shadowrocket
Available on non-China App Store accounts.
1. Switch to US/HK App Store
2. Purchase Shadowrocket ($2.99)
3. Import subscription URL from dashboard

### Windows: v2rayN
1. Download from GitHub
2. Import subscription URL
3. Enable **System Proxy**
4. Routing rule: **Bypass CN**

### macOS: V2Box or Clash

---

## DNS Configuration for China

Use these DNS servers in your VPN client:
- Primary: `8.8.8.8` (Google, through VPN)
- Secondary: `1.1.1.1` (Cloudflare, through VPN)
- Avoid: `114.114.114.114` (Chinese DNS, may leak)

**Enable DNS over HTTPS (DoH):**
```
https://dns.google/dns-query
https://cloudflare-dns.com/dns-query
```

---

## Routing Rules (Split Tunneling)

Configure your client to:
- Route **Chinese websites** directly (no VPN)
- Route **foreign websites** through VPN

This improves speed for accessing Chinese content while protecting foreign traffic.

```json
{
  "routing": {
    "rules": [
      {
        "type": "field",
        "ip": ["geoip:cn", "geoip:private"],
        "outboundTag": "direct"
      },
      {
        "type": "field",
        "domain": ["geosite:cn"],
        "outboundTag": "direct"
      }
    ]
  }
}
```

---

## Backup Connections

Always have 2-3 server configurations ready. If one is blocked:
1. Open your VPN app
2. Switch to a different server or protocol
3. Test connection

**Our servers auto-rotate protocols during GFW crackdowns.**

---

## 常见问题 (FAQ in Chinese)

**Q: 无法连接怎么办？**
A: 尝试切换到VLESS Reality协议，或者更换服务器节点。

**Q: 速度慢？**
A: 选择日本或新加坡服务器，使用Reality协议，开启BBR加速。

**Q: 什么时候会被封锁？**
A: 通常在政治敏感期间（两会、国庆等）封锁会加强，建议提前备好多个配置。
