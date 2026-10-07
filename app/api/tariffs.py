from fastapi import APIRouter, Depends

from app.api.deps import Repositories, get_repos
from app.api.schemas import TariffOut
from app.application import payments as payments_app

router = APIRouter(prefix="/tariffs", tags=["tariffs"])


@router.get("", response_model=list[TariffOut])
def list_tariffs(repos: Repositories = Depends(get_repos)):
    return payments_app.list_tariffs(repos.tariffs)
