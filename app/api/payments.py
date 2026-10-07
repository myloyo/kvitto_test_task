from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, Response, status

from app.api.deps import Repositories, get_repos
from app.api.schemas import PaymentCreate, PaymentOut
from app.application import payments as payments_app
from app.domain.enums import PaymentStatus

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("", response_model=PaymentOut)
def create_payment(
    payload: PaymentCreate,
    response: Response,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    repos: Repositories = Depends(get_repos),
):
    payment, created = payments_app.create_payment(
        repos.tariffs,
        repos.payments,
        tariff_id=payload.tariff_id,
        email=str(payload.email),
        method=payload.method,
        installment_months=payload.installment_months,
        promo_code=payload.promo_code,
        idempotency_key=idempotency_key,
    )
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return payment


@router.get("", response_model=list[PaymentOut])
def list_payments(
    email: str | None = None,
    status_: PaymentStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    repos: Repositories = Depends(get_repos),
):
    return payments_app.list_payments(
        repos.payments, email=email, status=status_, limit=limit, offset=offset
    )


@router.get("/{payment_id}", response_model=PaymentOut)
def get_payment(
    payment_id: int,
    repos: Repositories = Depends(get_repos),
):
    return payments_app.get_payment(repos.payments, payment_id)
