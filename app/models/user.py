from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
import uuid

if TYPE_CHECKING:
    from app.models.report import Report
    from app.models.saved_place import SavedPlace
    from app.models.search_history import SearchHistory


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    username: str
    email: Optional[str] = Field(index=True, unique=True)
    phone_number: Optional[str] = Field(default=None, index=True, unique=True)
    hashed_password: str

    created_at: datetime = Field(default_factory=datetime.utcnow)

    # 🔗 relationships
    reports: List["Report"] = Relationship(back_populates="user")
    search_history: List["SearchHistory"] = Relationship(back_populates="user")
    saved_places: List["SavedPlace"] = Relationship(back_populates="user")
