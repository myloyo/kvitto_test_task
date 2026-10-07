from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.domain.exceptions import (
    BankUnavailable,
    InvalidTransition,
    PaymentNotFound,
    TariffNotFound,
    UnknownPromoCode,
)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(TariffNotFound)
    async def tariff_not_found(_, __) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": "tariff not found"})

    @app.exception_handler(PaymentNotFound)
    async def payment_not_found(_, __) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": "payment not found"})

    @app.exception_handler(InvalidTransition)
    async def invalid_transition(_, __) -> JSONResponse:
        # Форма ответа из ТЗ, не стандартный FastAPI detail.
        return JSONResponse(status_code=409, content={"error": "invalid_transition"})

    @app.exception_handler(UnknownPromoCode)
    async def unknown_promo(_, __) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": "unknown promo code"})

    @app.exception_handler(BankUnavailable)
    async def bank_unavailable(_, __) -> JSONResponse:
        return JSONResponse(status_code=502, content={"detail": "bank unavailable"})
