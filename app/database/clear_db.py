import asyncio
import os
import sys
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from models import Base, Group, Student, Room, Question, Queue


async def clear_db():
    """Очистить все таблицы, кроме admins."""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("Ошибка: не задана переменная окружения DATABASE_URL")
        sys.exit(1)

    if database_url.startswith('postgresql://'):
        database_url = database_url.replace(
            'postgresql://', 'postgresql+asyncpg://', 1)

    engine = create_async_engine(database_url, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncSessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as session:
        # Порядок удаления важен из-за внешних ключей
        await session.execute(delete(Queue))
        await session.execute(delete(Question))
        await session.execute(delete(Room))
        await session.execute(delete(Student))
        await session.execute(delete(Group))
        await session.commit()

    print("✅ Очистка БД выполнена (кроме admins)")


async def main():
    await clear_db()


if __name__ == "__main__":
    asyncio.run(main())
