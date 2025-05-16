from pydantic import BaseModel, ConfigDict
from datetime import datetime

class FeedbackBase(BaseModel):
    feedback: str

class FeedbackCreate(FeedbackBase):
    pass

class Feedback(FeedbackBase):
    id: int
    deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class FeedbackOut(FeedbackBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
