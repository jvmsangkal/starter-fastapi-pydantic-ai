from sqlmodel import SQLModel

# Alembic and the test fixtures build tables from this metadata, so import every
# feature's table models here.
from app.items import models as items_models  # noqa: F401

metadata = SQLModel.metadata
