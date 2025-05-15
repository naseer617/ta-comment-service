from fastapi import FastAPI, HTTPException, Depends
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.exc import OperationalError
from sqlalchemy import select, update
from sqlalchemy.orm import declarative_base, mapped_column
from sqlalchemy import Integer, String, Boolean
from pydantic import BaseModel
import os

# Load env vars
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "comment_db")
DB_USER = os.getenv("DB_USER", "comment_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "secure_pw")
DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"

# SQLAlchemy setup
Base = declarative_base()
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# FastAPI app
app = FastAPI(title="Comment Service")

# Database Dependency
async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

# Models
class FeedbackDB(Base):
    __tablename__ = "feedbacks"

    id = mapped_column(Integer, primary_key=True, index=True)
    feedback = mapped_column(String, nullable=False)
    deleted = mapped_column(Boolean, default=False)

class FeedbackCreate(BaseModel):
    feedback: str

class FeedbackOut(BaseModel):
    id: int
    feedback: str

    class Config:
        orm_mode = True

# Routes
@app.on_event("startup")
async def startup():
    retries = 10
    for attempt in range(retries):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print("Database connected and initialized.")
            break
        except OperationalError as e:
            print(f" DB not ready (attempt {attempt + 1}/{retries}), retrying...")
            await asyncio.sleep(2)
    else:
        raise RuntimeError("Database failed to connect after multiple retries.")

@app.post("/comments", response_model=FeedbackOut)
async def create_feedback(payload: FeedbackCreate, session: AsyncSession = Depends(get_session)):
    new_fb = FeedbackDB(feedback=payload.feedback)
    session.add(new_fb)
    await session.commit()
    await session.refresh(new_fb)
    return new_fb

@app.get("/comments", response_model=list[FeedbackOut])
async def get_feedbacks(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(FeedbackDB).where(FeedbackDB.deleted == False))
    return result.scalars().all()

@app.delete("/comments")
async def soft_delete_feedbacks(session: AsyncSession = Depends(get_session)):
    await session.execute(update(FeedbackDB).values(deleted=True).where(FeedbackDB.deleted == False))
    await session.commit()
    return {"message": "Feedbacks soft deleted"}
