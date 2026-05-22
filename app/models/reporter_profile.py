from datetime import datetime
import uuid

from sqlmodel import Field, SQLModel


class ReporterProfile(SQLModel, table=True):
    __tablename__ = "reporter_profiles"

    user_id: uuid.UUID = Field(foreign_key="users.id", primary_key=True)
    trust_score: float = Field(default=0.5, ge=0.0, le=1.0)
    total_reports : int = Field(default=0, ge=0)
    last_updated: datetime = Field(default_factory=datetime.utcnow)