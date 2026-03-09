-- MAMA CHOL VPN - PostgreSQL Database Schema

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    phone VARCHAR(20),
    country VARCHAR(10) DEFAULT 'BD',
    language VARCHAR(10) DEFAULT 'en',
    currency VARCHAR(10) DEFAULT 'BDT',
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    referral_code VARCHAR(20) UNIQUE,
    referred_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Servers table
CREATE TABLE servers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    host VARCHAR(255) NOT NULL,
    port INTEGER NOT NULL,
    location VARCHAR(100),
    country VARCHAR(10),
    protocol VARCHAR(50) DEFAULT 'vless',
    is_active BOOLEAN DEFAULT TRUE,
    max_users INTEGER DEFAULT 500,
    current_users INTEGER DEFAULT 0,
    bandwidth_limit_gb INTEGER,
    bandwidth_used_gb FLOAT DEFAULT 0,
    uptime_percent FLOAT DEFAULT 100,
    ping_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Subscriptions table
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan VARCHAR(20) NOT NULL CHECK (plan IN ('bronze', 'silver', 'gold', 'platinum')),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'expired', 'cancelled', 'grace')),
    started_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    bandwidth_limit_gb INTEGER,
    bandwidth_used_gb FLOAT DEFAULT 0,
    auto_renew BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- VPN configs table
CREATE TABLE vpn_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    server_id UUID REFERENCES servers(id),
    config_link TEXT NOT NULL,
    uuid VARCHAR(36) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    last_used TIMESTAMP
);

-- Payments table
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    subscription_id UUID REFERENCES subscriptions(id),
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(10) NOT NULL,
    method VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed', 'refunded')),
    transaction_id VARCHAR(255),
    gateway_response JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Support tickets table
CREATE TABLE support_tickets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    subject VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
    priority VARCHAR(10) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Promo codes table
CREATE TABLE promo_codes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(50) UNIQUE NOT NULL,
    discount_percent INTEGER CHECK (discount_percent BETWEEN 1 AND 100),
    max_uses INTEGER,
    used_count INTEGER DEFAULT 0,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Referrals table
CREATE TABLE referrals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    referrer_id UUID NOT NULL REFERENCES users(id),
    referred_id UUID NOT NULL REFERENCES users(id),
    reward_amount DECIMAL(10,2),
    reward_paid BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_subscriptions_user ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_payments_user ON payments(user_id);
CREATE INDEX idx_vpn_configs_user ON vpn_configs(user_id);
CREATE INDEX idx_support_tickets_user ON support_tickets(user_id);
