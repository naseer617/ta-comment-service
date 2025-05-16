import pytest
from pydantic import ValidationError
from app.schemas import FeedbackCreate

def test_feedback_create_validation():
    with pytest.raises(ValidationError):
        FeedbackCreate()  # missing required "feedback"

    # valid
    fb = FeedbackCreate(feedback="Great service!")
    assert fb.feedback == "Great service!"
