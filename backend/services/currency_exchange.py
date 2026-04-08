"""Currency exchange service with Redis caching."""
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Optional
import aiohttp
import redis.asyncio as aioredis
from backend.config.settings import settings

logger = logging.getLogger(__name__)

CACHE_KEY = "mamachol:exchange_rates"
CACHE_META_KEY = "mamachol:exchange_rates:meta"
LAST_GOOD_KEY = "mamachol:exchange_rates:last_good"
CACHE_TTL = 1800  # 30 minutes

# 2026 approximate fallback rates (USD base)
FALLBACK_RATES: Dict[str, float] = {
    "USD": 1.0, "BDT": 121.0, "CNY": 7.1, "INR": 84.0,
    "EUR": 0.91, "GBP": 0.78, "JPY": 151.0, "SGD": 1.33,
    "MYR": 4.45, "THB": 34.5, "AED": 3.67, "SAR": 3.75,
    "BTC": 0.000011, "ETH": 0.00034, "USDT": 1.0, "USDC": 1.0
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

        rates, source = await self._fetch_rates()

        try:
            r = await self.get_redis()
            await r.setex(CACHE_KEY, settings.exchange_rate_cache_ttl, json.dumps(rates))
            meta = {
                "source": source,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "cached": True,
            }
            await r.setex(CACHE_META_KEY, settings.exchange_rate_cache_ttl, json.dumps(meta))
            # Persist last-good rates indefinitely so we have them if all APIs fail
            await r.set(LAST_GOOD_KEY, json.dumps({"rates": rates, "source": source}))
        except Exception:
            pass

        return rates

    async def get_rates_with_meta(self) -> dict:
        """Return rates plus metadata (source, cached flag, updated_at)."""
        try:
            r = await self.get_redis()
            cached_rates = await r.get(CACHE_KEY)
            cached_meta = await r.get(CACHE_META_KEY)
            if cached_rates and cached_meta:
                return {
                    "base": "USD",
                    "rates": json.loads(cached_rates),
                    **json.loads(cached_meta),
                }
        except Exception as e:
            logger.warning(f"Redis unavailable: {e}")

        rates, source = await self._fetch_rates()
        now = datetime.now(timezone.utc).isoformat()

        try:
            r = await self.get_redis()
            await r.setex(CACHE_KEY, settings.exchange_rate_cache_ttl, json.dumps(rates))
            meta = {"source": source, "updated_at": now, "cached": False}
            await r.setex(CACHE_META_KEY, settings.exchange_rate_cache_ttl, json.dumps(meta))
            await r.set(LAST_GOOD_KEY, json.dumps({"rates": rates, "source": source}))
        except Exception:
            pass

        return {"base": "USD", "rates": rates, "source": source, "cached": False, "updated_at": now}

    async def _fetch_rates(self) -> tuple[Dict[str, float], str]:
        """Fetch rates from 3 free, unlimited, no-API-key APIs in priority order."""
        apis = [
            # Priority 1: fawazahmed0 CDN-backed, 200+ currencies, unlimited, no key
            "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.json",
            # Priority 2: Frankfurter (Central bank rates, 163+ currencies, unlimited, no key)
            "https://api.frankfurter.app/latest?base=USD",
            # Priority 3: ExConvert (Real-time, 145+ fiat, unlimited, no key)
            "https://exconvert.com/api/convert?base=USD",
        ]

        for url in apis:
            try:
                async with aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as session:
                    async with session.get(url) as resp:
                        if resp.status != 200:
                            continue
                        data = await resp.json(content_type=None)
                        rates = self._parse_api_response(url, data)
                        if rates and "BDT" in rates:
                            logger.info(f"Exchange rates fetched from {url}")
                            source = self._source_name(url)
                            return rates, source
            except Exception as e:
                logger.warning(f"Exchange API {url} failed: {e}")

        # Try last-good rates before falling back to hardcoded values
        try:
            r = await self.get_redis()
            last_good_raw = await r.get(LAST_GOOD_KEY)
            if last_good_raw:
                last_good = json.loads(last_good_raw)
                logger.warning("All live APIs failed — using last-good cached rates")
                return last_good["rates"], f"last_good({last_good.get('source', 'unknown')})"
        except Exception:
            pass

        logger.warning("Using hardcoded fallback exchange rates")
        return FALLBACK_RATES.copy(), "fallback"

    def _parse_api_response(self, url: str, data: dict) -> Optional[Dict[str, float]]:
        """Parse API-specific response formats and normalize keys to UPPERCASE."""
        try:
            if url.startswith("https://cdn.jsdelivr.net/npm/@fawazahmed0/"):
                # Format: {"date": "...", "usd": {"bdt": 121.0, "cny": 7.1, ...}}
                raw = data.get("usd", {})
                if not raw:
                    return None
                return {k.upper(): float(v) for k, v in raw.items() if isinstance(v, (int, float))}

            if url.startswith("https://api.frankfurter.app/"):
                # Format: {"base": "USD", "rates": {"BDT": 121.0, "CNY": 7.1, ...}}
                # Note: USD itself is not included; add it manually
                raw = data.get("rates", {})
                if not raw:
                    return None
                rates = {k.upper(): float(v) for k, v in raw.items() if isinstance(v, (int, float))}
                rates["USD"] = 1.0
                return rates

            if url.startswith("https://exconvert.com/"):
                # Format: {"base": "USD", "results": {"BDT": {"rate": 121.0}, ...}}
                # or simpler: {"BDT": 121.0, ...} — try both
                raw = data.get("results", data)
                if not raw:
                    return None
                rates: Dict[str, float] = {}
                for k, v in raw.items():
                    if k in ("base", "date", "success"):
                        continue
                    if isinstance(v, dict):
                        rate = v.get("rate") or v.get("value") or v.get("val")
                        if rate is not None:
                            rates[k.upper()] = float(rate)
                    elif isinstance(v, (int, float)):
                        rates[k.upper()] = float(v)
                if rates:
                    rates["USD"] = 1.0
                return rates if rates else None

        except Exception as e:
            logger.warning(f"Failed to parse response from {url}: {e}")
        return None

    @staticmethod
    def _source_name(url: str) -> str:
        if url.startswith("https://cdn.jsdelivr.net/npm/@fawazahmed0/"):
            return "fawazahmed0"
        if url.startswith("https://api.frankfurter.app/"):
            return "frankfurter"
        if url.startswith("https://exconvert.com/"):
            return "exconvert"
        return "unknown"

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
