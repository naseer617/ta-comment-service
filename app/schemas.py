from pydantic import BaseModel, ConfigDict

class FeedbackCreate(BaseModel):
    feedback: str

class FeedbackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # Pydantic v2 style

    id: int
    feedback: str
