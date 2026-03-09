# MAMA CHOL VPN — Admin Manual

## Accessing the Admin Panel

URL: `https://mamachol.online/admin`
Default credentials are set during installation.

---

## Dashboard Overview

The admin dashboard shows:
- **Total Users** — active and inactive accounts
- **Monthly Revenue** — broken down by payment method
- **Active Connections** — real-time VPN sessions
- **Server Load** — CPU, RAM, bandwidth per server

---

## User Management

### View All Users
Navigate to **Admin → Users** to see a paginated table of all users with:
- Username, email, registration date
- Current plan and expiry
- Total payments made
- Account status (active/suspended/banned)

### Edit User
Click any user row to edit:
- Reset password
- Change plan / extend expiry
- Add data quota
- Suspend or ban account

### Bulk Actions
Select multiple users to:
- Send email notification
- Extend subscription
- Export to CSV

---

## Subscription Management

Navigate to **Admin → Subscriptions**:
- View all active/expired subscriptions
- Manually create subscription for offline payments
- Apply promo codes
- Set auto-renewal reminders

---

## Server Management

Navigate to **Admin → Servers**:
- Add/remove VPN servers
- View per-server statistics
- Restart X-UI service remotely
- Configure load balancing weights

### Adding a New Server
1. Click **Add Server**
2. Enter: IP, SSH port, X-UI URL, credentials
3. Select VPN protocols to enable
4. Set geographic location and flag
5. Click Save — server will be auto-tested

---

## Payment Management

Navigate to **Admin → Payments**:
- View all transactions (success/failed/pending)
- Manually verify offline payments
- Issue refunds
- Export payment reports

### Handling Failed Payments
1. Filter by status: **Failed**
2. Check payment gateway logs
3. If confirmed paid, click **Mark as Paid**
4. User will receive activation email automatically

---

## Promo Codes

Navigate to **Admin → Promo Codes**:
- Create discount codes (% or fixed amount)
- Set usage limits and expiry dates
- Track usage statistics

---

## Analytics

Navigate to **Admin → Analytics**:
- Revenue trends (daily/weekly/monthly)
- User growth charts
- Popular payment methods
- Geographic distribution of users
- Peak usage hours

---

## System Settings

Navigate to **Admin → Settings**:
- Update payment gateway credentials
- Configure email templates
- Set maintenance mode
- Manage API keys
- Configure Telegram bot settings
