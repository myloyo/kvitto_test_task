import json
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from app.api.deps import Repositories, get_repos
from app.api.schemas import WebhookIn, WebhookOut
from app.application import payments as payments_app
from app.infrastructure.bank_provider import confirm_payment_with_bank
from app.infrastructure.config import get_settings
from app.infrastructure.security import verify_signature

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/bank")
async def bank_webhook(
    request: Request,
    x_signature: str | None = Header(default=None, alias="X-Signature"),
    repos: Repositories = Depends(get_repos),
):
    settings = get_settings()
    body = await request.body()

    if settings.webhook_verify_signature and not verify_signature(
        settings.webhook_secret, body, x_signature
    ):
        raise HTTPException(status_code=401, detail="invalid signature")

    try:
        raw = json.loads(body) if body else {}
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=422, detail="invalid json") from exc

    payload = WebhookIn.model_validate(raw)

    if settings.bank_confirm_on_webhook:
        confirmed = await confirm_payment_with_bank(payload.payment_id)
        if confirmed is None:
            raise HTTPException(status_code=502, detail="bank unavailable")
        logger.info(
            "банк подтвердил payment=%s status=%s",
            payload.payment_id,
            confirmed.status,
        )

    payments_app.apply_status_change(repos.payments, payload.payment_id, payload.status)
    return WebhookOut()
