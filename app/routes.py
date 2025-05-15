from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from shared.db.connection import get_session
from .models import FeedbackDB
from .schemas import FeedbackCreate, FeedbackOut

router = APIRouter()

@router.post("/comments", response_model=FeedbackOut)
async def create_feedback(payload: FeedbackCreate, session: AsyncSession = Depends(get_session)):
    new_fb = FeedbackDB(feedback=payload.feedback)
    session.add(new_fb)
    await session.commit()
    await session.refresh(new_fb)
    return new_fb

@router.get("/comments", response_model=list[FeedbackOut])
async def get_feedbacks(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(FeedbackDB).where(FeedbackDB.deleted == False))
    return result.scalars().all()

@router.delete("/comments")
async def soft_delete_feedbacks(session: AsyncSession = Depends(get_session)):
    await session.execute(update(FeedbackDB).values(deleted=True).where(FeedbackDB.deleted == False))
    await session.commit()
    return {"message": "Feedbacks soft deleted"}
