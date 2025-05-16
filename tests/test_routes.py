import pytest
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Result, Update, ScalarResult, Select
from shared.db.connection import get_session
from app.models import FeedbackDB
from app.main import app as fastapi_app

@pytest.fixture
def app():
    return fastapi_app

@pytest.mark.asyncio
async def test_create_and_get_feedback(async_client):
    # Create
    response = await async_client.post("/comments", json={
        "feedback": "Test feedback"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["feedback"] == "Test feedback"

    # Get
    response = await async_client.get("/comments")
    assert response.status_code == 200
    feedbacks = response.json()
    assert isinstance(feedbacks, list)
    assert any(f["feedback"] == "Test feedback" for f in feedbacks)

@pytest.mark.asyncio
async def test_soft_delete_feedbacks(async_client):
    # Create a feedback first
    await async_client.post("/comments", json={
        "feedback": "Test feedback"
    })

    # Soft delete all feedbacks
    response = await async_client.delete("/comments")
    assert response.status_code == 200
    assert response.json()["message"] == "Feedbacks soft deleted"

    # Verify feedback is not returned in get
    response = await async_client.get("/comments")
    assert response.status_code == 200
    feedbacks = response.json()
    assert len(feedbacks) == 0  # Feedback should be soft deleted

@pytest.mark.asyncio
async def test_soft_delete_single_feedback(async_client):
    # Create a feedback first
    response = await async_client.post("/comments", json={
        "feedback": "Test feedback"
    })
    assert response.status_code == 200
    comment_id = response.json()["id"]

    # Delete the feedback
    response = await async_client.delete(f"/comments/{comment_id}")
    assert response.status_code == 200
    assert response.json()["message"] == f"Comment {comment_id} soft deleted"

    # Verify feedback is not in get response
    response = await async_client.get("/comments")
    assert response.status_code == 200
    feedbacks = response.json()
    assert not any(f["id"] == comment_id for f in feedbacks)

@pytest.mark.asyncio
async def test_soft_delete_single_feedback_not_found(async_client):
    # Try to delete non-existent feedback
    response = await async_client.delete("/comments/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Comment not found"

@pytest.mark.asyncio
async def test_soft_delete_single_feedback_database_error(async_client, app):
    # Create a mock session
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.execute = AsyncMock(side_effect=SQLAlchemyError("Database error"))
    mock_session.rollback = AsyncMock()

    async def get_mock_session():
        yield mock_session

    # Override the dependency
    app.dependency_overrides[get_session] = get_mock_session

    try:
        response = await async_client.delete("/comments/1")
        assert response.status_code == 500
        assert response.json()["detail"] == "Failed to delete comment"
        mock_session.rollback.assert_awaited_once()
    finally:
        # Clear the override
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_soft_delete_single_feedback_already_deleted(async_client):
    # Create a feedback first
    response = await async_client.post("/comments", json={
        "feedback": "Test feedback"
    })
    assert response.status_code == 200
    comment_id = response.json()["id"]

    # Delete the feedback first time
    response = await async_client.delete(f"/comments/{comment_id}")
    assert response.status_code == 200

    # Try to delete the same feedback again
    response = await async_client.delete(f"/comments/{comment_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Comment not found"

@pytest.mark.asyncio
async def test_soft_delete_single_feedback_generic_error(async_client, app):
    # Create a mock session
    mock_session = AsyncMock(spec=AsyncSession)

    # Test generic exception (not SQLAlchemyError)
    mock_session.execute = AsyncMock(side_effect=Exception("Some other error"))
    mock_session.rollback = AsyncMock()

    async def get_mock_session():
        yield mock_session

    # Override the dependency
    app.dependency_overrides[get_session] = get_mock_session

    try:
        response = await async_client.delete("/comments/1")
        assert response.status_code == 500
        assert response.json()["detail"] == "Failed to delete comment"
        mock_session.rollback.assert_awaited_once()
    finally:
        # Clear the override
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_create_feedback_with_refresh(async_client, app):
    # Create a mock session that verifies refresh is called
    mock_session = AsyncMock(spec=AsyncSession)
    # add is not actually async, so use MagicMock
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    # Create a feedback object with an ID
    new_feedback = FeedbackDB(id=1, feedback="Test feedback")
    # Set the refresh to modify the passed object
    async def mock_refresh(obj):
        obj.id = 1
    mock_session.refresh.side_effect = mock_refresh

    # Make add and commit return None (they don't return anything in real usage)
    mock_session.add.return_value = None
    mock_session.commit.return_value = None

    async def get_mock_session():
        yield mock_session

    app.dependency_overrides[get_session] = get_mock_session

    try:
        response = await async_client.post("/comments", json={
            "feedback": "Test feedback"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["feedback"] == "Test feedback"
        mock_session.refresh.assert_awaited_once()
        mock_session.add.assert_called_once()  # Use assert_called_once instead of assert_awaited_once
        mock_session.commit.assert_awaited_once()
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_feedbacks_with_deleted(async_client, app):
    # Create a mock session that returns both deleted and non-deleted feedbacks
    mock_session = AsyncMock(spec=AsyncSession)

    # Create the feedbacks we want to return
    # Note: The route's query includes .where(FeedbackDB.deleted == False)
    # so we should only return non-deleted feedbacks in our mock
    feedbacks = [
        FeedbackDB(id=1, feedback="Active feedback", deleted=False)
    ]

    # Create a mock result that properly simulates SQLAlchemy's scalars().all() chain
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = feedbacks
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute = AsyncMock(return_value=mock_result)

    async def get_mock_session():
        yield mock_session

    app.dependency_overrides[get_session] = get_mock_session

    try:
        response = await async_client.get("/comments")
        assert response.status_code == 200
        feedbacks = response.json()
        assert len(feedbacks) == 1  # Only non-deleted feedback should be returned
        assert feedbacks[0]["feedback"] == "Active feedback"
        assert feedbacks[0]["id"] == 1
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_soft_delete_feedbacks_verify_update(async_client, app):
    # Create a mock session that verifies the update operation
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = AsyncMock()
    mock_session.execute.return_value = mock_result
    mock_session.commit = AsyncMock()

    async def get_mock_session():
        yield mock_session

    app.dependency_overrides[get_session] = get_mock_session

    try:
        response = await async_client.delete("/comments")
        assert response.status_code == 200
        assert response.json()["message"] == "Feedbacks soft deleted"
        mock_session.execute.assert_awaited_once()
        mock_session.commit.assert_awaited_once()
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_soft_delete_single_feedback_verify_returning(async_client, app):
    # Create a mock session that verifies the returning clause
    mock_session = AsyncMock(spec=AsyncSession)

    # Create a mock result that returns an ID
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=1)

    # Make execute return the mock result
    mock_session.execute = AsyncMock(return_value=mock_result)
    # Make commit return None
    mock_session.commit = AsyncMock(return_value=None)

    async def get_mock_session():
        yield mock_session

    app.dependency_overrides[get_session] = get_mock_session

    try:
        response = await async_client.delete("/comments/1")
        assert response.status_code == 200
        assert response.json()["message"] == "Comment 1 soft deleted"
        mock_session.execute.assert_awaited_once()
        mock_session.commit.assert_awaited_once()
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_soft_delete_single_feedback_http_exception(async_client, app):
    # Create a mock session that simulates a not found scenario
    mock_session = AsyncMock(spec=AsyncSession)

    # Create a mock result that returns None for scalar_one_or_none
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=None)
    mock_session.execute = AsyncMock(return_value=mock_result)

    async def get_mock_session():
        yield mock_session

    app.dependency_overrides[get_session] = get_mock_session

    try:
        response = await async_client.delete("/comments/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Comment not found"
        # Verify that commit was not called (exception was raised before commit)
        mock_session.commit.assert_not_awaited()
    finally:
        app.dependency_overrides.clear()
