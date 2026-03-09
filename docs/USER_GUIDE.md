# MAMA CHOL VPN — User Guide

## Getting Started

### Creating an Account

1. Visit [mamachol.online](https://mamachol.online)
2. Click **Sign Up** in the top right
3. Enter your email address and create a password
4. Verify your email (check spam folder)
5. You're in! Start with a free trial or choose a plan.

---

## Choosing a Plan

| Plan | Duration | Bangladesh | Features |
|------|----------|-----------|---------|
| Basic | 1 Month | ৳70 | 1 device, 50GB |
| Standard | 3 Months | ৳180 | 3 devices, 150GB |
| Premium | 6 Months | ৳300 | 5 devices, unlimited |

---

## Making a Payment

### bKash
1. Go to Dashboard → **Upgrade Plan**
2. Select **bKash**
3. Enter your bKash number
4. Approve payment in your bKash app
5. Plan activates within 30 seconds

### Nagad
1. Select **Nagad** at checkout
2. Enter your Nagad number
3. Confirm in Nagad app
4. Instant activation

### Card (Stripe)
1. Select **Credit/Debit Card**
2. Enter card details securely
3. Instant activation

---

## Setting Up Your VPN

### Android
1. Install **V2RayNG** from Play Store
2. Go to Dashboard → **My Config**
3. Tap **Show QR Code**
4. In V2RayNG: tap `+` → **Import from QRCode**
5. Tap the config → **Connect**

### iOS
1. Install **Shadowrocket** from App Store ($2.99)
2. Go to Dashboard → **My Config**
3. Tap **Show QR Code**
4. Scan with Shadowrocket
5. Tap **Connect**

### Windows
1. Download **v2rayN** from our [Download page](https://mamachol.online/download)
2. Extract and run v2rayN.exe
3. Go to Dashboard → **My Config** → **Copy Link**
4. In v2rayN: Servers → **Import from clipboard**
5. Press **Ctrl+Enter** to connect

### macOS
1. Install **V2Box** from Mac App Store
2. Import config from QR code or link
3. Toggle VPN on

### Linux
```bash
# Install v2ray
bash <(curl -L https://raw.githubusercontent.com/v2fly/fhs-install-v2ray/master/install-release.sh)

# Import your config (from Dashboard → My Config → Download JSON)
sudo cp your-config.json /usr/local/etc/v2ray/config.json
sudo systemctl start v2ray
```

---

## Dashboard Features

### Connection Status
Your dashboard shows your current connection status, IP address, and data usage in real-time.

### Devices
Manage which devices are connected. You can:
- View active sessions
- Disconnect a specific device remotely
- Add a new device (within your plan limit)

### Data Usage
Monitor your monthly data usage with a visual progress bar.

### Support
Open a ticket or chat with our AI assistant for instant help.

---

## VPN Modes Explained

| Mode | Best For | Speed | Stability |
|------|---------|-------|-----------|
| VLESS Reality | China users | ⚡⚡⚡ | ⭐⭐⭐ |
| VMess WebSocket | General use | ⚡⚡ | ⭐⭐⭐ |
| Trojan gRPC | Low latency | ⚡⚡⚡ | ⭐⭐ |
| Shadowsocks | Fastest | ⚡⚡⚡⚡ | ⭐⭐ |

---

## Troubleshooting

**Can't connect?**
1. Check your internet connection
2. Try a different VPN mode
3. Regenerate your config in Dashboard → My Config → **Regenerate**
4. Contact support if still not working

**Slow speeds?**
- Switch to VLESS Reality mode
- Try a server in a different region
- Check your plan's data limit

**Payment not reflected?**
- Wait 5 minutes — payments may take time to process
- Check your email for confirmation
- Contact support with your transaction ID
