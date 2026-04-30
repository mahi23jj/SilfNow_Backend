import datetime
from typing import Optional
import uuid

from pydantic import Field
from sqlmodel import Relationship, SQLModel

from app.models.user import User

from sqlmodel import SQLModel


class SavedPlace(SQLModel, table=True):
    __tablename__ = "saved_places"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    user_id: uuid.UUID = Field(foreign_key="users.id")
    node_id: uuid.UUID = Field(foreign_key="nodes.id")

    name: str

    # 🔗 relationship
    user: Optional[User] = Relationship(back_populates="saved_places")
