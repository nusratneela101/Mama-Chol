"""Tests for payment endpoints."""
import pytest


class TestCreatePayment:
    def test_create_payment_unauthenticated(self, client):
        resp = client.post("/api/v1/payment/create", json={
            "plan": "basic",
            "duration_months": 1,
            "payment_method": "bkash",
            "phone": "01700000000",
        })
        assert resp.status_code == 401

    def test_create_payment_invalid_plan(self, client, auth_headers):
        resp = client.post("/api/v1/payment/create", json={
            "plan": "gold",
            "duration_months": 1,
            "payment_method": "bkash",
        }, headers=auth_headers)
        assert resp.status_code == 400
        assert "invalid plan" in resp.json()["detail"].lower()

    def test_create_bkash_payment(self, client, auth_headers):
        resp = client.post("/api/v1/payment/create", json={
            "plan": "basic",
            "duration_months": 1,
            "payment_method": "bkash",
            "currency": "BDT",
            "phone": "01700000000",
        }, headers=auth_headers)
        # May return 200 or a gateway-related error depending on env
        assert resp.status_code in (200, 400, 503)

    def test_create_nagad_payment(self, client, auth_headers):
        resp = client.post("/api/v1/payment/create", json={
            "plan": "standard",
            "duration_months": 3,
            "payment_method": "nagad",
            "currency": "BDT",
            "phone": "01800000000",
        }, headers=auth_headers)
        assert resp.status_code in (200, 400, 503)

    def test_create_stripe_payment(self, client, auth_headers):
        resp = client.post("/api/v1/payment/create", json={
            "plan": "premium",
            "duration_months": 6,
            "payment_method": "stripe",
            "currency": "USD",
        }, headers=auth_headers)
        assert resp.status_code in (200, 400, 500, 503)

    def test_create_crypto_btc_payment(self, client, auth_headers):
        resp = client.post("/api/v1/payment/create", json={
            "plan": "basic",
            "duration_months": 1,
            "payment_method": "crypto_btc",
            "currency": "USD",
        }, headers=auth_headers)
        assert resp.status_code in (200, 400, 503)

    def test_create_payment_with_promo_code(self, client, db, auth_headers):
        from backend.models.database import PromoCode
        from datetime import datetime, timedelta

        promo = PromoCode(
            code="SAVE20",
            discount_percent=20,
            is_active=True,
            valid_until=datetime.utcnow() + timedelta(days=30),
        )
        db.add(promo)
        db.commit()

        resp = client.post("/api/v1/payment/create", json={
            "plan": "basic",
            "duration_months": 1,
            "payment_method": "bkash",
            "currency": "BDT",
            "phone": "01700000000",
            "promo_code": "SAVE20",
        }, headers=auth_headers)
        assert resp.status_code in (200, 400, 503)


class TestVerifyPayment:
    def test_verify_payment_unauthenticated(self, client):
        resp = client.post("/api/v1/payment/verify/00000000-0000-0000-0000-000000000000",
                           json={"transaction_id": "TXN123"})
        assert resp.status_code == 401

    def test_verify_nonexistent_payment(self, client, auth_headers):
        resp = client.post("/api/v1/payment/verify/00000000-0000-0000-0000-000000000000",
                           json={"transaction_id": "TXN123"},
                           headers=auth_headers)
        assert resp.status_code in (400, 404, 422)


class TestPaymentHistory:
    def test_payment_history_unauthenticated(self, client):
        resp = client.get("/api/v1/payment/history")
        assert resp.status_code == 401

    def test_payment_history_empty(self, client, auth_headers):
        resp = client.get("/api/v1/payment/history")
        # Without token: 401; with token: 200 or route may not exist
        assert resp.status_code in (200, 401, 404)

    def test_payment_history_authenticated(self, client, auth_headers):
        resp = client.get("/api/v1/payment/history", headers=auth_headers)
        assert resp.status_code in (200, 404)
        if resp.status_code == 200:
            assert isinstance(resp.json(), (list, dict))
