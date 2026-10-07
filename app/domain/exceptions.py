class AppError(Exception):
    """Общий предок ошибок бизнеса. API превращает их в HTTP-ответы."""


class TariffNotFound(AppError):
    pass


class PaymentNotFound(AppError):
    pass


class InvalidTransition(AppError):
    pass


class UnknownPromoCode(AppError):
    pass


class DuplicateIdempotencyKey(AppError):
    pass


class BankUnavailable(AppError):
    pass
