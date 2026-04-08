"""Currency exchange rate API endpoint."""
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.services.currency_exchange import currency_service

router = APIRouter()


@router.get("/rates", tags=["Currency"])
async def get_exchange_rates():
    """
    Return live USD-based exchange rates.

    Rates are fetched from free, no-API-key APIs in priority order:
    1. fawazahmed0 (CDN-backed, 200+ currencies)
    2. Frankfurter (Central bank rates, 163+ currencies)
    3. ExConvert (Real-time, 145+ fiat + 300+ crypto)

    Results are cached in Redis for 30 minutes.
    """
    try:
        data = await currency_service.get_rates_with_meta()
        return data
    except Exception:
        return JSONResponse(
            status_code=500,
            content={"detail": "Failed to fetch exchange rates. Please try again later."},
        )
