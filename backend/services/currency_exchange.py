"""Currency exchange service with Redis caching."""
import json
import logging
from typing import Dict, Optional
import aiohttp
import redis.asyncio as aioredis
from backend.config.settings import settings

logger = logging.getLogger(__name__)

CACHE_KEY = "mamachol:exchange_rates"
CACHE_TTL = 3600  # 1 hour

FALLBACK_RATES: Dict[str, float] = {
    "USD": 1.0, "BDT": 110.0, "CNY": 7.24, "INR": 83.5,
    "EUR": 0.92, "GBP": 0.79, "JPY": 149.5, "SGD": 1.34,
    "MYR": 4.67, "THB": 35.1, "AED": 3.67, "SAR": 3.75,
    "BTC": 0.000024, "ETH": 0.00038, "USDT": 1.0, "USDC": 1.0
}

FIXED_PRICES = {
    "basic":    {"BDT": 70, "USD": 4.99, "CNY": 9.90, "INR": 99},
    "standard": {"BDT": 180, "USD": 9.99, "CNY": 19.90, "INR": 199},
    "premium":  {"BDT": 300, "USD": 14.99, "CNY": 29.90, "INR": 349},
}

CURRENCY_SYMBOLS = {
    "USD": "$", "BDT": "৳", "CNY": "¥", "INR": "₹",
    "EUR": "€", "GBP": "£", "JPY": "¥", "BTC": "₿",
    "ETH": "Ξ", "USDT": "₮"
}


class CurrencyService:
    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None

    async def get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = await aioredis.from_url(settings.redis_url, decode_responses=True)
        return self._redis

    async def get_rates(self) -> Dict[str, float]:
        """Get exchange rates, using cache if available."""
        try:
            r = await self.get_redis()
            cached = await r.get(CACHE_KEY)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Redis unavailable: {e}")

        rates = await self._fetch_rates()
        try:
            r = await self.get_redis()
            await r.setex(CACHE_KEY, CACHE_TTL, json.dumps(rates))
        except Exception:
            pass
        return rates

    async def _fetch_rates(self) -> Dict[str, float]:
        """Fetch rates from free API."""
        apis = [
            f"https://open.er-api.com/v6/latest/USD",
            f"https://api.exchangerate-api.com/v4/latest/USD",
        ]
        for url in apis:
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            rates = data.get("rates", {})
                            if rates and "BDT" in rates:
                                logger.info("Exchange rates fetched from API")
                                return rates
            except Exception as e:
                logger.warning(f"Exchange API {url} failed: {e}")
        logger.warning("Using fallback exchange rates")
        return FALLBACK_RATES.copy()

    async def convert(self, amount: float, from_currency: str, to_currency: str) -> float:
        """Convert amount between currencies."""
        if from_currency == to_currency:
            return amount
        rates = await self.get_rates()
        from_rate = rates.get(from_currency, FALLBACK_RATES.get(from_currency, 1))
        to_rate = rates.get(to_currency, FALLBACK_RATES.get(to_currency, 1))
        usd_amount = amount / from_rate
        return round(usd_amount * to_rate, 6)

    async def get_plan_price(self, plan: str, currency: str) -> float:
        """Get plan price in specified currency."""
        # Use fixed prices for main currencies
        if plan in FIXED_PRICES and currency in FIXED_PRICES[plan]:
            return FIXED_PRICES[plan][currency]
        # Convert from USD for other currencies
        usd_price = FIXED_PRICES.get(plan, {}).get("USD", 0.0)
        return await self.convert(usd_price, "USD", currency)

    def format_price(self, amount: float, currency: str) -> str:
        """Format price with currency symbol."""
        symbol = CURRENCY_SYMBOLS.get(currency, currency)
        if currency in ("BTC", "ETH"):
            return f"{symbol}{amount:.6f}"
        if currency == "JPY":
            return f"{symbol}{int(amount):,}"
        if currency in ("BDT", "INR"):
            return f"{symbol}{int(amount):,}"
        return f"{symbol}{amount:.2f}"


currency_service = CurrencyService()
