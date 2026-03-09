# 🛡️ MAMA CHOL VPN

**AI-Powered Multi-Mode VPN Service** — Fast, Secure, and Built for Bangladesh, China, India & Beyond

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)

---

## 🌐 Live Demo
- **Website:** https://mamachol.online
- **Admin Panel:** https://mamachol.online/admin

---

## ✨ Features

- 🔒 **4 VPN Modes:** VLESS Reality, VMess WebSocket, Trojan GRPC, Shadowsocks
- 🤖 **AI Assistant:** Powered by Ollama (Mistral), supports EN/BN/ZH/HI/AR
- 🌍 **Multi-Language:** English, Bengali, Chinese, Hindi, Arabic
- 💳 **Multi-Currency Payments:** bKash, Nagad, Stripe, Crypto (BTC/ETH/USDT)
- 📱 **Cross-Platform:** Android, iOS, Windows, macOS, Linux
- 🇨🇳 **China Optimized:** Bypasses GFW with Reality & obfuscation
- 📊 **Real-time Dashboard:** Usage stats, QR codes, device management
- 🔔 **Telegram Bot:** Account management via Telegram

---

## 💰 Pricing

| Plan | Bangladesh | China | USA | India |
|------|-----------|-------|-----|-------|
| Basic (1 Month) | ৳70 | ¥9.90 | $4.99 | ₹99 |
| Standard (3 Months) | ৳180 | ¥19.90 | $9.99 | ₹199 |
| Premium (6 Months) | ৳300 | ¥29.90 | $14.99 | ₹349 |

---

## 🚀 Quick Start

### Prerequisites
- Ubuntu 22.04+ (Oracle Cloud Free Tier recommended)
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Node.js 18+

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/Mama-Chol.git
cd Mama-Chol

# Run the automated install script
chmod +x server-setup/install.sh
sudo ./server-setup/install.sh

# Configure environment
cp .env.example .env
nano .env

# Start services
docker-compose -f deployment/docker-compose.yml up -d
```

---

## 📁 Project Structure

```
Mama-Chol/
├── frontend/          # Static HTML/CSS/JS frontend
│   ├── index.html     # Homepage
│   ├── pages/         # Feature, pricing, download pages
│   ├── dashboard/     # User dashboard
│   └── admin/         # Admin panel
├── backend/           # FastAPI Python backend
│   ├── api/           # API route handlers
│   ├── models/        # SQLAlchemy models
│   ├── services/      # Business logic
│   ├── utils/         # Utilities
│   └── config/        # Configuration
├── chatbot/           # Telegram bot & web widget
├── server-setup/      # Server installation scripts
├── database/          # SQL schemas & migrations
├── tests/             # Test suite
├── deployment/        # Docker Compose & Dockerfile
└── docs/              # Documentation
```

---

## 📚 Documentation

- [Setup Guide](docs/SETUP_GUIDE.md)
- [Admin Manual](docs/ADMIN_MANUAL.md)
- [User Guide](docs/USER_GUIDE.md)
- [API Documentation](docs/API_DOCUMENTATION.md)
- [China Setup](docs/CHINA_SETUP.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML5, CSS3, Vanilla JS |
| Backend | Python 3.11, FastAPI |
| Database | PostgreSQL 15 |
| Cache | Redis 7 |
| VPN Core | X-UI, V2Ray, Xray-core |
| AI | Ollama (Mistral) |
| Payments | bKash, Nagad, Stripe |
| Deploy | Docker, Nginx, HAProxy |

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

Pull requests are welcome! See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

---

*Made with ❤️ for users who need fast, reliable, and affordable VPN access worldwide.*
