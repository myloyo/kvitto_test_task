import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

import httpx

from app.domain.exceptions import BankUnavailable
from app.infrastructure.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class BankPaymentPayload:
    payment_id: int
    status: str
    raw: dict[str, Any] = field(default_factory=dict)


class BankProvider:
    RETRYABLE_STATUS = {429, 500, 502, 503, 504}

    def __init__(
        self,
        base_url: str | None = None,
        *,
        attempts: int | None = None,
        base_delay: float | None = None,
        timeout: float | None = None,
        transport: httpx.BaseTransport | httpx.AsyncBaseTransport | None = None,
    ) -> None:
        settings = get_settings()
        self.base_url = base_url or settings.bank_base_url
        self.attempts = attempts if attempts is not None else settings.bank_retry_attempts
        self.base_delay = (
            base_delay if base_delay is not None else settings.bank_retry_base_delay
        )
        self.timeout = timeout if timeout is not None else settings.bank_timeout
        self._transport = transport
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "BankProvider":
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            transport=self._transport,
        )
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def fetch_payment_payload(self, payment_id: int) -> BankPaymentPayload:
        if self._client is None:
            raise RuntimeError("BankProvider открывают через `async with`")

        last_error: Exception | None = None
        for attempt in range(1, self.attempts + 1):
            try:
                response = await self._client.get(f"/payments/{payment_id}")
                if response.status_code in self.RETRYABLE_STATUS:
                    raise httpx.HTTPStatusError(
                        f"банк вернул {response.status_code}",
                        request=response.request,
                        response=response,
                    )
                response.raise_for_status()
                data = response.json()
                return BankPaymentPayload(
                    payment_id=payment_id,
                    status=str(data.get("status", "unknown")),
                    raw=data,
                )
            except httpx.HTTPStatusError as exc:
                last_error = exc
                # 4xx кроме 429 — ошибка запроса, повторять бессмысленно.
                if exc.response.status_code not in self.RETRYABLE_STATUS:
                    raise BankUnavailable(str(exc)) from exc
            except httpx.TransportError as exc:
                last_error = exc

            if attempt < self.attempts:
                delay = self.base_delay * (2 ** (attempt - 1))
                logger.warning(
                    "банк payment=%s попытка %s/%s: %s; пауза %.3fs",
                    payment_id,
                    attempt,
                    self.attempts,
                    last_error,
                    delay,
                )
                await asyncio.sleep(delay)

        raise BankUnavailable(
            f"банк недоступен после {self.attempts} попыток: {last_error}"
        ) from last_error


async def confirm_payment_with_bank(payment_id: int) -> BankPaymentPayload | None:
    provider = BankProvider()
    async with provider:
        try:
            return await provider.fetch_payment_payload(payment_id)
        except BankUnavailable:
            logger.warning("не удалось подтвердить платёж %s в банке", payment_id)
            return None
