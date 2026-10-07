from enum import Enum


class PaymentMethod(str, Enum):
    card = "card"
    sbp = "sbp"
    installment = "installment"


class PaymentStatus(str, Enum):
    pending = "pending"
    succeeded = "succeeded"
    failed = "failed"
    refunded = "refunded"


# Какие статусы можно поставить следующим. Остальное — InvalidTransition.
ALLOWED_TRANSITIONS: dict[PaymentStatus, set[PaymentStatus]] = {
    PaymentStatus.pending: {PaymentStatus.succeeded, PaymentStatus.failed},
    PaymentStatus.succeeded: {PaymentStatus.refunded},
    PaymentStatus.failed: set(),
    PaymentStatus.refunded: set(),
}


def can_transition(current: PaymentStatus, target: PaymentStatus) -> bool:
    return target in ALLOWED_TRANSITIONS.get(current, set())
