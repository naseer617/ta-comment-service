from pydantic import BaseModel

class FeedbackCreate(BaseModel):
    feedback: str

class FeedbackOut(BaseModel):
    id: int
    feedback: str

    class Config:
        from_attributes = True  # Pydantic v2
