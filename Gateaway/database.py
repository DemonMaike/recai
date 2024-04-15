from typing import AsyncGenerator
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from models import Base, Task, Audio, DiaraziedText, Report
from models import Base

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost/postgres"


engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
