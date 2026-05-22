from datetime import datetime

from sqlmodel import Field, SQLModel


class SystemState(SQLModel, table=True):
    __tablename__ = "system_state"

    key: str = Field(primary_key=True)
    value: datetime = Field(default_factory=datetime.utcnow)