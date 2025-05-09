from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from utils.singletonmeta import SingletonMeta


class Database(metaclass=SingletonMeta):
    def __init__(self, url: str):
        self.engine = create_async_engine(url)
        self.sessionmaker = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def create_db_and_tables(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    def get_session(self) -> AsyncSession:
        return self.sessionmaker()
