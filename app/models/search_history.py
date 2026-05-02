from datetime import datetime
from typing import Optional, TYPE_CHECKING
import uuid

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.user import User


class SearchHistory(SQLModel, table=True):
    __tablename__ = "search_history"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    user_id: uuid.UUID = Field(foreign_key="users.id")

    start_node_id: uuid.UUID = Field(foreign_key="nodes.id")
    end_node_id: uuid.UUID = Field(foreign_key="nodes.id")

    searched_at: datetime = Field(default_factory=datetime.utcnow)

    # 🔗 relationship
    user: Optional["User"] = Relationship(back_populates="search_history")
