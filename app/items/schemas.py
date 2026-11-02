from sqlmodel import SQLModel


class ItemCreate(SQLModel):
    id: int | None = None
    name: str
