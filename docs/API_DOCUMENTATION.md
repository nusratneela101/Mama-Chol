# MAMA CHOL VPN — API Documentation

Base URL: `https://mamachol.online/api/v1`

All requests require `Content-Type: application/json` header.
Protected endpoints require `Authorization: Bearer <token>` header.

---

## Authentication

### POST /auth/register
Register a new user.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "full_name": "John Doe",
  "referral_code": "FRIEND10"
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

### POST /auth/login
Login with email and password.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### POST /auth/refresh
Refresh access token.

**Request:**
```json
{
  "refresh_token": "eyJ..."
}
```

### POST /auth/logout
Invalidate current token. **(Protected)**

---

## User

### GET /user/profile
Get current user profile. **(Protected)**

**Response (200):**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "plan": "premium",
  "plan_expiry": "2025-06-01T00:00:00Z",
  "data_used_gb": 12.5,
  "data_limit_gb": 150,
  "devices_connected": 2,
  "devices_limit": 3
}
```

### GET /user/dashboard
Get dashboard statistics. **(Protected)**

### GET /user/vpn-config
Get VPN configuration. **(Protected)**

**Response (200):**
```json
{
  "vless_reality_link": "vless://...",
  "vmess_ws_link": "vmess://...",
  "trojan_grpc_link": "trojan://...",
  "shadowsocks_link": "ss://...",
  "qr_code_base64": "data:image/png;base64,...",
  "subscription_url": "https://mamachol.online/sub/uuid"
}
```

### POST /user/regenerate-config
Regenerate VPN keys. **(Protected)**

---

## VPN

### GET /vpn/servers
List available servers.

**Response (200):**
```json
[
  {
    "id": 1,
    "name": "Bangladesh-01",
    "location": "Dhaka",
    "country_code": "BD",
    "flag": "🇧🇩",
    "latency_ms": 15,
    "load_percent": 45,
    "online": true
  }
]
```

### POST /vpn/connect
**(Protected)** Connect to VPN server.

**Request:**
```json
{
  "server_id": 1,
  "protocol": "vless_reality"
}
```

### POST /vpn/disconnect
**(Protected)** Disconnect from VPN.

### GET /vpn/usage
**(Protected)** Get data usage statistics.

---

## Payment

### POST /payment/create
**(Protected)** Create a new payment.

**Request:**
```json
{
  "plan": "premium",
  "duration_months": 6,
  "payment_method": "bkash",
  "currency": "BDT",
  "phone": "01XXXXXXXXX"
}
```

**Response (200):**
```json
{
  "payment_id": "PAY-uuid",
  "gateway_url": "https://...",
  "amount": 300,
  "currency": "BDT",
  "expires_at": "2025-01-01T00:30:00Z"
}
```

### GET /payment/history
**(Protected)** Get payment history.

### POST /payment/webhook/bkash
bKash payment webhook (server-to-server).

### POST /payment/webhook/nagad
Nagad payment webhook.

### POST /payment/webhook/stripe
Stripe payment webhook.

### GET /payment/verify/{payment_id}
**(Protected)** Verify payment status.

---

## Admin Endpoints

All admin endpoints require admin role.

### GET /admin/users
List all users with pagination.

**Query params:** `page`, `limit`, `search`, `status`

### PATCH /admin/users/{user_id}
Update user (suspend, change plan, etc.)

### GET /admin/analytics
Get platform analytics.

### POST /admin/servers
Add a new VPN server.

### DELETE /admin/servers/{server_id}
Remove a VPN server.

### GET /admin/payments
List all payments.

---

## Error Responses

```json
{
  "detail": "Error message here",
  "code": "ERROR_CODE",
  "status": 400
}
```

Common error codes:
- `AUTH_INVALID` — Invalid credentials
- `TOKEN_EXPIRED` — Access token expired
- `PLAN_REQUIRED` — Feature requires active plan
- `PAYMENT_FAILED` — Payment processing failed
- `QUOTA_EXCEEDED` — Data quota exceeded
