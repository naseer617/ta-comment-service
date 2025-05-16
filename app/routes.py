from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from shared.db.connection import get_session
from shared.utils.logging import log_exceptions
import logging
from .models import FeedbackDB
from .schemas import FeedbackCreate, FeedbackOut

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/comments", response_model=FeedbackOut)
@log_exceptions
async def create_feedback(payload: FeedbackCreate, session: AsyncSession = Depends(get_session)):
    try:
        logger.info("Creating new feedback: %s", payload.feedback)
        new_fb = FeedbackDB(feedback=payload.feedback)
        session.add(new_fb)
        logger.info("Added feedback to session")
        await session.commit()
        logger.info("Committed session")
        await session.refresh(new_fb)
        logger.info("Refreshed feedback object")
        return new_fb
    except IntegrityError as e:
        logger.error("Integrity error in create_feedback: %s", str(e))
        await session.rollback()
        if "duplicate key" in str(e).lower():
            raise HTTPException(status_code=400, detail="Comment already exists")
        raise HTTPException(status_code=400, detail="Database error")
    except SQLAlchemyError as e:
        logger.error("Database error in create_feedback: %s", str(e))
        await session.rollback()
        raise HTTPException(status_code=500, detail="Failed to create comment")

@router.get("/comments", response_model=list[FeedbackOut])
@log_exceptions
async def get_feedbacks(session: AsyncSession = Depends(get_session)):
    try:
        logger.info("Fetching all feedbacks")
        result = await session.execute(select(FeedbackDB).where(FeedbackDB.deleted == False))
        feedbacks = result.scalars().all()
        logger.info("Found %d feedbacks", len(feedbacks) if feedbacks else 0)
        return feedbacks or []  # Return empty list if None
    except SQLAlchemyError as e:
        logger.error("Database error in get_feedbacks: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch comments")

@router.delete("/comments")
@log_exceptions
async def soft_delete_feedbacks(session: AsyncSession = Depends(get_session)):
    try:
        logger.info("Soft deleting all feedbacks")
        await session.execute(update(FeedbackDB).values(deleted=True).where(FeedbackDB.deleted == False))
        await session.commit()
        logger.info("Successfully soft deleted all feedbacks")
        return {"message": "Feedbacks soft deleted"}
    except SQLAlchemyError as e:
        logger.error("Database error in soft_delete_feedbacks: %s", str(e))
        await session.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete comments")

@router.delete("/comments/{comment_id}")
@log_exceptions
async def soft_delete_feedback(comment_id: int, session: AsyncSession = Depends(get_session)):
    try:
        logger.info("Soft deleting feedback %d", comment_id)
        result = await session.execute(
            update(FeedbackDB)
            .values(deleted=True)
            .where(FeedbackDB.id == comment_id, FeedbackDB.deleted == False)
            .returning(FeedbackDB.id)
        )
        deleted_id = result.scalar_one_or_none()
        if not deleted_id:
            logger.info("Feedback %d not found", comment_id)
            raise HTTPException(status_code=404, detail="Comment not found")
        await session.commit()
        logger.info("Successfully soft deleted feedback %d", comment_id)
        return {"message": f"Comment {comment_id} soft deleted"}
    except HTTPException:
        # Let HTTP exceptions (like 404) pass through
        raise
    except SQLAlchemyError as e:
        logger.error("Database error in soft_delete_feedback: %s", str(e))
        await session.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete comment")
