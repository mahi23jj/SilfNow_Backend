from typing import Optional, TYPE_CHECKING
import uuid

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.user import User


class SavedPlace(SQLModel, table=True):
    __tablename__ = "saved_places"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    user_id: uuid.UUID = Field(foreign_key="users.id")
    node_id: uuid.UUID = Field(foreign_key="nodes.id")

    name: str

    # 🔗 relationship
    user: Optional["User"] = Relationship(back_populates="saved_places")
