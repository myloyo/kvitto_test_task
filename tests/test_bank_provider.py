import httpx
import pytest

from app.domain.exceptions import BankUnavailable
from app.infrastructure.bank_provider import BankProvider


@pytest.mark.asyncio
async def test_fetch_payment_payload_returns_status():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/payments/7"
        return httpx.Response(200, json={"status": "succeeded", "id": 7})

    async with BankProvider(
        base_url="https://bank.test",
        transport=httpx.MockTransport(handler),
        attempts=1,
    ) as bank:
        payload = await bank.fetch_payment_payload(7)

    assert payload.payment_id == 7
    assert payload.status == "succeeded"
    assert payload.raw["id"] == 7


@pytest.mark.asyncio
async def test_retries_retryable_status_then_succeeds():
    calls = {"n": 0}

    def handler(_: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(503)
        return httpx.Response(200, json={"status": "pending"})

    async with BankProvider(
        base_url="https://bank.test",
        transport=httpx.MockTransport(handler),
        attempts=3,
        base_delay=0,
    ) as bank:
        payload = await bank.fetch_payment_payload(1)

    assert calls["n"] == 3
    assert payload.status == "pending"


@pytest.mark.asyncio
async def test_client_error_does_not_retry():
    calls = {"n": 0}

    def handler(_: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(404)

    async with BankProvider(
        base_url="https://bank.test",
        transport=httpx.MockTransport(handler),
        attempts=3,
        base_delay=0,
    ) as bank:
        with pytest.raises(BankUnavailable):
            await bank.fetch_payment_payload(1)

    assert calls["n"] == 1


@pytest.mark.asyncio
async def test_exhausted_retries_raise_bank_unavailable():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(502)

    async with BankProvider(
        base_url="https://bank.test",
        transport=httpx.MockTransport(handler),
        attempts=2,
        base_delay=0,
    ) as bank:
        with pytest.raises(BankUnavailable):
            await bank.fetch_payment_payload(1)
