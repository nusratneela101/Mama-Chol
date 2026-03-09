"""AI Chatbot service using Ollama with multi-language support."""
import logging
import aiohttp
import json
from typing import Optional, AsyncGenerator
from backend.config.settings import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPTS = {
    "en": """You are a helpful customer support AI assistant for MAMA CHOL VPN service.
You help users with: VPN setup, payment issues, connectivity problems, plan selection, and general questions.
Key info: Plans are Basic (৳70/$4.99), Standard (৳180/$9.99), Premium (৳300/$14.99).
Payment methods: bKash, Nagad, Stripe, Crypto.
VPN protocols: VLESS Reality, VMess WebSocket, Trojan gRPC, Shadowsocks.
Be friendly, concise, and helpful. If you can't solve something, direct to support@mamachol.online.""",

    "bn": """আপনি MAMA CHOL VPN সেবার একটি সহায়ক গ্রাহক সেবা AI সহকারী।
আপনি ব্যবহারকারীদের সাহায্য করেন: VPN সেটআপ, পেমেন্ট সমস্যা, সংযোগ সমস্যা, প্ল্যান নির্বাচন।
মূল তথ্য: প্ল্যান হল বেসিক (৳70), স্ট্যান্ডার্ড (৳180), প্রিমিয়াম (৳300)।
পেমেন্ট: bKash, Nagad, Stripe, Crypto। বন্ধুত্বপূর্ণ এবং সংক্ষিপ্ত হন।""",

    "zh": """你是MAMA CHOL VPN服务的客户支持AI助手。
帮助用户解决：VPN设置、付款问题、连接问题、套餐选择等。
主要信息：套餐有基础版(¥9.90)、标准版(¥19.90)、高级版(¥29.90)。
支付方式：支付宝、微信支付、Stripe、加密货币。请友善简洁地回答。""",

    "hi": """आप MAMA CHOL VPN सेवा के लिए एक सहायक ग्राहक सेवा AI सहायक हैं।
उपयोगकर्ताओं की मदद करें: VPN सेटअप, भुगतान समस्याएं, कनेक्टिविटी समस्याएं।
मुख्य जानकारी: Basic (₹99), Standard (₹199), Premium (₹349)। मित्रवत और संक्षिप्त रहें।""",

    "ar": """أنت مساعد ذكاء اصطناعي لخدمة عملاء MAMA CHOL VPN.
تساعد المستخدمين في: إعداد VPN، مشاكل الدفع، مشاكل الاتصال، اختيار الخطة.
معلومات رئيسية: الخطط هي Basic ($4.99)، Standard ($9.99)، Premium ($14.99).
طرق الدفع: بطاقة ائتمان، عملة مشفرة. كن ودوداً وموجزاً."""
}

FALLBACK_RESPONSES = {
    "en": "I'm having trouble connecting to the AI right now. For immediate assistance, please contact support@mamachol.online or visit our Help Center.",
    "bn": "আমি এখন AI-এর সাথে সংযোগ করতে সমস্যায় পড়ছি। সাহায্যের জন্য support@mamachol.online-এ যোগাযোগ করুন।",
    "zh": "我目前无法连接到AI服务。请联系 support@mamachol.online 获取帮助。",
    "hi": "मुझे अभी AI से जुड़ने में परेशानी हो रही है। कृपया support@mamachol.online पर संपर्क करें।",
    "ar": "أواجه صعوبة في الاتصال بالذكاء الاصطناعي الآن. يرجى التواصل مع support@mamachol.online للحصول على المساعدة."
}


class AIChatbot:
    """AI chatbot powered by Ollama."""

    def __init__(self):
        self.base_url = settings.ollama_url
        self.model = settings.ollama_model

    async def _is_available(self) -> bool:
        """Check if Ollama service is running."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=3)) as session:
                async with session.get(f"{self.base_url}/api/tags") as resp:
                    return resp.status == 200
        except Exception:
            return False

    async def chat(self, message: str, lang: str = "en", history: Optional[list] = None) -> str:
        """Get AI response for a message."""
        if not await self._is_available():
            logger.warning("Ollama unavailable, using fallback")
            return FALLBACK_RESPONSES.get(lang, FALLBACK_RESPONSES["en"])

        system_prompt = SYSTEM_PROMPTS.get(lang, SYSTEM_PROMPTS["en"])
        messages = [{"role": "system", "content": system_prompt}]

        if history:
            messages.extend(history[-6:])  # Keep last 3 exchanges

        messages.append({"role": "user", "content": message})

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {"temperature": 0.7, "max_tokens": 400}
                }
                async with session.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data["message"]["content"].strip()
                    else:
                        logger.error(f"Ollama returned status {resp.status}")
                        return FALLBACK_RESPONSES.get(lang, FALLBACK_RESPONSES["en"])
        except aiohttp.ClientError as e:
            logger.error(f"Ollama chat error: {e}")
            return FALLBACK_RESPONSES.get(lang, FALLBACK_RESPONSES["en"])

    async def stream_chat(self, message: str, lang: str = "en") -> AsyncGenerator[str, None]:
        """Stream AI response tokens."""
        system_prompt = SYSTEM_PROMPTS.get(lang, SYSTEM_PROMPTS["en"])
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            "stream": True
        }
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
                async with session.post(f"{self.base_url}/api/chat", json=payload) as resp:
                    if resp.status == 200:
                        async for line in resp.content:
                            line = line.decode().strip()
                            if line:
                                try:
                                    data = json.loads(line)
                                    token = data.get("message", {}).get("content", "")
                                    if token:
                                        yield token
                                except json.JSONDecodeError:
                                    pass
        except Exception as e:
            logger.error(f"Ollama stream error: {e}")
            yield FALLBACK_RESPONSES.get(lang, FALLBACK_RESPONSES["en"])


chatbot = AIChatbot()
