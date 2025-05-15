from sqlalchemy import Integer, String, Boolean
from sqlalchemy.orm import mapped_column
from shared.db.base import Base

class FeedbackDB(Base):
    __tablename__ = "feedbacks"

    id = mapped_column(Integer, primary_key=True, index=True)
    feedback = mapped_column(String, nullable=False)
    deleted = mapped_column(Boolean, default=False)
