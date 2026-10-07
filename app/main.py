import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import select

from app.api import payments, tariffs, webhooks
from app.api.exception_handlers import register_exception_handlers
from app.domain.tariffs import DEFAULT_TARIFFS
from app.infrastructure.database import Base, SessionLocal, engine
from app.infrastructure.models import TariffModel

logging.basicConfig(level=logging.INFO)


def seed_tariffs() -> None:
    with SessionLocal() as db:
        existing_ids = set(db.scalars(select(TariffModel.id)).all())
        for row in DEFAULT_TARIFFS:
            if row["id"] not in existing_ids:
                db.add(TariffModel(**row))
        db.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    # create_all удобен для локального запуска. В проде обычно alembic upgrade head.
    Base.metadata.create_all(bind=engine)
    seed_tariffs()
    yield


app = FastAPI(title="Kvitto Payments", version="1.0.0", lifespan=lifespan)
register_exception_handlers(app)

app.include_router(tariffs.router)
app.include_router(payments.router)
app.include_router(webhooks.router)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
