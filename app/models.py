from sqlalchemy import Integer, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from shared.db.base import Base

class FeedbackDB(Base):
    __tablename__ = "feedbacks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    feedback: Mapped[str] = mapped_column(String, nullable=False)
    deleted: Mapped[bool] = mapped_column(Boolean, default=False)
