-- Migration 001: Initial schema
-- Run: psql -U postgres -d mamachol -f 001_initial.sql

\i ../schema.sql

-- Seed default server
INSERT INTO servers (name, host, port, location, country, protocol)
VALUES ('HK-01', 'hk1.mamachol.online', 443, 'Hong Kong', 'HK', 'vless');

-- Seed admin user (password: change-me)
INSERT INTO users (email, username, hashed_password, full_name, is_admin)
VALUES ('admin@mamachol.online', 'admin',
        '$2b$12$placeholder_change_this_hash', 'Administrator', TRUE);
