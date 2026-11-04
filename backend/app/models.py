from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Photo(Base):
    __tablename__ = "photos"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    author_name: Mapped[str] = mapped_column(String(40))
    width: Mapped[int]
    height: Mapped[int]
    orientation: Mapped[str] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    deleted: Mapped[bool] = mapped_column(Boolean, default=False)