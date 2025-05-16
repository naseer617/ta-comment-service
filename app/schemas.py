from pydantic import BaseModel, ConfigDict

class FeedbackCreate(BaseModel):
    feedback: str

class FeedbackOut(BaseModel):
    id: int
    feedback: str

    model_config = ConfigDict(from_attributes=True)  # Enables ORM serialization
