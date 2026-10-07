from dataclasses import dataclass

from fastapi import Depends
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.infrastructure.repositories import (
    SqlAlchemyPaymentRepository,
    SqlAlchemyTariffRepository,
)


@dataclass
class Repositories:
    # Одна сессия на запрос: оба репозитория видят одни и те же данные.
    tariffs: SqlAlchemyTariffRepository
    payments: SqlAlchemyPaymentRepository


def get_repos(db: Session = Depends(get_db)) -> Repositories:
    return Repositories(
        tariffs=SqlAlchemyTariffRepository(db),
        payments=SqlAlchemyPaymentRepository(db),
    )
