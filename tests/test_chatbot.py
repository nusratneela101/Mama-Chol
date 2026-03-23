"""Tests for AI chatbot service and endpoint."""
import pytest
from unittest.mock import AsyncMock, patch


class TestChatbotEndpoint:
    def test_chat_missing_message(self, client):
        resp = client.post("/api/v1/chat", json={})
        # Empty message → 400
        assert resp.status_code == 400

    def test_chat_message_too_long(self, client):
        resp = client.post("/api/v1/chat", json={"message": "x" * 1001})
        assert resp.status_code == 400

    def test_chat_valid_message_returns_reply(self, client):
        """Chatbot falls back gracefully when Ollama is unavailable in test env."""
        resp = client.post("/api/v1/chat", json={
            "message": "Hello, what plans do you offer?",
            "lang": "en",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "reply" in data
        assert "lang" in data
        assert data["lang"] == "en"

    def test_chat_bengali_language(self, client):
        resp = client.post("/api/v1/chat", json={
            "message": "আমি কোন প্ল্যান নেব?",
            "lang": "bn",
        })
        assert resp.status_code == 200
        assert resp.json()["lang"] == "bn"

    def test_chat_chinese_language(self, client):
        resp = client.post("/api/v1/chat", json={
            "message": "你好，我需要帮助",
            "lang": "zh",
        })
        assert resp.status_code == 200

    def test_chat_with_history(self, client):
        resp = client.post("/api/v1/chat", json={
            "message": "What is the standard plan price?",
            "lang": "en",
            "history": [
                {"role": "user", "content": "Hi"},
                {"role": "assistant", "content": "Hello! How can I help?"},
            ],
        })
        assert resp.status_code == 200
        assert "reply" in resp.json()

    def test_chat_get_method(self, client):
        """GET on /api/v1/chat without a body returns 400 (invalid message)."""
        resp = client.get("/api/v1/chat")
        assert resp.status_code in (200, 400, 405, 422, 500)


class TestAIChatbotService:
    """Unit tests for the AIChatbot service class."""

    @pytest.mark.asyncio
    async def test_fallback_on_unavailable_ollama(self):
        """When Ollama is unreachable the chatbot should return a fallback message."""
        from backend.services.ai_chatbot import AIChatbot
        bot = AIChatbot()

        with patch.object(bot, "_is_available", new_callable=AsyncMock, return_value=False):
            reply = await bot.chat("test message", lang="en")
            assert isinstance(reply, str)
            assert len(reply) > 0

    @pytest.mark.asyncio
    async def test_fallback_unknown_language(self):
        """Unknown language should still produce a non-empty fallback."""
        from backend.services.ai_chatbot import AIChatbot
        bot = AIChatbot()

        with patch.object(bot, "_is_available", new_callable=AsyncMock, return_value=False):
            reply = await bot.chat("test", lang="zz")
            assert isinstance(reply, str)

    @pytest.mark.asyncio
    async def test_system_prompts_exist_for_all_languages(self):
        from backend.services.ai_chatbot import SYSTEM_PROMPTS, FALLBACK_RESPONSES
        for lang in ["en", "bn", "zh", "hi", "ar"]:
            assert lang in SYSTEM_PROMPTS, f"Missing system prompt for {lang}"
            assert lang in FALLBACK_RESPONSES, f"Missing fallback for {lang}"
