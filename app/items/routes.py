from fastapi import APIRouter

from app.db.session import SessionDep
from app.items import service
from app.items.models import Item
from app.items.schemas import ItemCreate

router = APIRouter(prefix='/items')


@router.post('')
def create_item(data: ItemCreate, session: SessionDep) -> Item:
    return service.create_item(session, data)


@router.get('')
def list_items(session: SessionDep) -> list[Item]:
    return service.list_items(session)


@router.get('/{item_id}')
def get_item(item_id: int, session: SessionDep) -> Item:
    return service.get_item(session, item_id)
