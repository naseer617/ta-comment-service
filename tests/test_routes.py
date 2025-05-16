import pytest

@pytest.mark.asyncio
async def test_create_and_get_feedback(async_client):
    # Create feedback
    response = await async_client.post("/comments", json={"feedback": "Test feedback"})
    assert response.status_code == 200
    data = response.json()
    assert data["feedback"] == "Test feedback"

    # Get feedback
    response = await async_client.get("/comments")
    assert response.status_code == 200
    feedbacks = response.json()
    assert isinstance(feedbacks, list)
    assert any(f["feedback"] == "Test feedback" for f in feedbacks)
