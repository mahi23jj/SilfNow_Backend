"""Database package."""


from fastapi.params import Depends
from sqlmodel import create_engine , Session, SQLModel
from typing import Annotated, Optional

from app.core.config import settings


engine = create_engine(settings.postgres_url, pool_pre_ping=True)

def get_session() -> Session: # type: ignore
    """Get a new database session."""
    with Session(engine) as session:
        yield session


SessionType = Annotated[Session, Depends(get_session)]



