from sqlmodel import Session, select

from app.core.errors import ConflictError, NotFoundError
from app.items.models import Item
from app.items.schemas import ItemCreate


def create_item(session: Session, data: ItemCreate) -> Item:
    if data.id is not None and session.get(Item, data.id) is not None:
        raise ConflictError(f'Item {data.id} already exists')
    item = Item.model_validate(data)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def list_items(session: Session) -> list[Item]:
    return list(session.exec(select(Item)).all())


def get_item(session: Session, item_id: int) -> Item:
    item = session.get(Item, item_id)
    if item is None:
        raise NotFoundError(f'Item {item_id} not found')
    return item
