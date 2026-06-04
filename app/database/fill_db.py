import asyncio
import sys
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import delete
from models import Base, Group, Student, Room, Question, Queue, Admin
from faker import Faker
import random


async def init_db(limit=100):
    """
    Асинхронно инициализирует базу данных тестовыми данными
    Args:
        limit (int): количество тестовых записей для генерации
    """
    # Получаем URL базы данных из переменных окружения
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("Ошибка: не задана переменная окружения DATABASE_URL")
        sys.exit(1)

    # Преобразуем URL для asyncpg (если используется PostgreSQL)
    if database_url.startswith('postgresql://'):
        database_url = database_url.replace(
            'postgresql://', 'postgresql+asyncpg://', 1)

    # Создаем асинхронное подключение к базе данных
    engine = create_async_engine(database_url, echo=False)

    # Создаем таблицы (если их нет)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Создаем асинхронную сессию
    AsyncSessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with AsyncSessionLocal() as session:
        # Очищаем существующие данные (опционально)
        await session.execute(delete(Queue))
        await session.execute(delete(Question))
        await session.execute(delete(Room))
        await session.execute(delete(Student))
        await session.execute(delete(Group))
        await session.execute(delete(Admin))
        await session.commit()

        fake = Faker()

        # Создаем группы
        groups = []
        group_names = ["Group A", "Group B", "Group C", "Group D"]
        for name in group_names:
            group = Group(name=name)
            session.add(group)
            groups.append(group)
        await session.commit()

        # Создаем студентов
        students = []
        for i in range(limit):
            student = Student(
                name=fake.name(),
                tg_id=random.randint(100000000, 999999999),
                id_group=random.choice(groups).id
            )
            session.add(student)
            students.append(student)
        await session.commit()

        # Создаем комнаты
        rooms = []
        for group in groups:
            for i in range(3):  # 3 комнаты на группу
                room = Room(
                    name=f"Room {fake.word().capitalize()} {i+1}",
                    id_group=group.id
                )
                session.add(room)
                rooms.append(room)
        await session.commit()

        # Создаем вопросы для комнат
        questions = []
        for room in rooms:
            for i in range(5):  # 5 вопросов на комнату
                question = Question(
                    text=fake.sentence(),
                    wrong_answer1=fake.sentence(),
                    wrong_answer2=fake.sentence(),
                    wrong_answer3=fake.sentence(),
                    correct_answer=fake.sentence(),
                    id_room=room.id
                )
                session.add(question)
                questions.append(question)
        await session.commit()

        # Создаем очереди
        for room in rooms:
            # Берем случайных студентов для этой очереди
            room_students = random.sample(students, min(10, len(students)))
            for position, student in enumerate(room_students, 1):
                queue = Queue(
                    id_student=student.id,
                    position=position,
                    id_room=room.id,
                    points=random.randint(0, 100)
                )
                session.add(queue)
        await session.commit()

        # Создаем администраторов
        for i in range(3):
            admin = Admin(
                tg_id=random.randint(100000000, 999999999)
            )
            session.add(admin)
        await session.commit()

        # Получаем статистику для вывода
        groups_count = len(groups)
        students_count = len(students)
        rooms_count = len(rooms)
        questions_count = len(questions)

        # Получаем количество записей в очередях
        queue_result = await session.execute(delete(Queue).returning(Queue.id))
        queue_count = len(queue_result.scalars().all())

        admin_result = await session.execute(delete(Admin).returning(Admin.id))
        admin_count = len(admin_result.scalars().all())

        print(f"База данных успешно заполнена тестовыми данными!")
        print(f"Создано:")
        print(f"  - Групп: {groups_count}")
        print(f"  - Студентов: {students_count}")
        print(f"  - Комнат: {rooms_count}")
        print(f"  - Вопросов: {questions_count}")
        print(f"  - Записей в очередях: {queue_count}")
        print(f"  - Администраторов: {admin_count}")


async def main():
    """Основная асинхронная функция"""
    # Получаем аргумент из командной строки (количество записей)
    limit = 100
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            print(f"Использование: python {sys.argv[0]} [limit]")
            sys.exit(1)

    await init_db(limit)


if __name__ == "__main__":
    # Запускаем асинхронную функцию
    asyncio.run(main())
