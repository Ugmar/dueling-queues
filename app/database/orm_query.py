from sqlalchemy import select, func, desc, and_, text, update, delete
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Group, Student, Room, Question, Queue, Admin
from typing import List, Optional, Tuple, Dict, Any

# ==================== CRUD ====================


async def create_object(session: AsyncSession, model_class, **kwargs):
    """Создание нового объекта"""
    obj = model_class(**kwargs)
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


async def get_object_by_id(session: AsyncSession, model_class, obj_id: int):
    """Получение объекта по ID"""
    stmt = select(model_class).where(model_class.id == obj_id)
    result = await session.execute(stmt)
    return result.scalars().first()


async def get_all_objects(session: AsyncSession, model_class, skip: int = 0, limit: int = 100):
    """Получение всех объектов с пагинацией"""
    stmt = select(model_class).offset(skip).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


async def update_object(session: AsyncSession, obj, **kwargs):
    """Обновление объекта"""
    for key, value in kwargs.items():
        setattr(obj, key, value)
    await session.commit()
    await session.refresh(obj)
    return obj


async def delete_object(session: AsyncSession, obj):
    """Удаление объекта"""
    await session.delete(obj)
    await session.commit()


# ==================== Группы ====================

async def get_group_by_name(session: AsyncSession, name: str) -> Optional[Group]:
    """Получение группы по названию"""
    stmt = select(Group).where(Group.name == name)
    result = await session.execute(stmt)
    return result.scalars().first()


async def get_groups_with_students_count(session: AsyncSession) -> List[Tuple[Group, int]]:
    """Получение групп с количеством студентов"""
    stmt = select(
        Group,
        func.count(Student.id).label('students_count')
    ).outerjoin(Student).group_by(Group.id)
    result = await session.execute(stmt)
    return result.all()


async def get_group_with_rooms(session: AsyncSession, group_id: int) -> Optional[Group]:
    """Получение группы со всеми комнатами"""
    stmt = select(Group).options(
        selectinload(Group.rooms)
    ).where(Group.id == group_id)
    result = await session.execute(stmt)
    return result.scalars().first()


# ==================== Студенты ====================


async def get_student_by_tg_id(session: AsyncSession, tg_id: int) -> Optional[Student]:
    """Получение студента по Telegram ID"""
    stmt = select(Student).options(
        joinedload(Student.group)
    ).where(Student.tg_id == tg_id)
    result = await session.execute(stmt)
    return result.scalars().unique().first()


async def get_students_by_group(session: AsyncSession, group_id: int) -> List[Student]:
    """Получение всех студентов группы"""
    stmt = select(Student).where(Student.id_group == group_id)
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_students_with_group(session: AsyncSession, limit: int = 10) -> Optional[Student]:
    """Получение студента с информацией о группе"""
    stmt = select(Student).options(
        joinedload(Student.group)
    ).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().unique().all()


async def create_student(session: AsyncSession, name: str, tg_id: int, group_id: int) -> Student:
    """Создание нового студента"""
    student = Student(name=name, tg_id=tg_id, id_group=group_id)
    session.add(student)
    await session.commit()
    await session.refresh(student)
    return student


# async def get_students_without_tg_id(session: AsyncSession) -> List[Student]:
#     """Получение студентов без привязанного Telegram аккаунта"""
#     stmt = select(Student).where(Student.tg_id.is_(None))
#     result = await session.execute(stmt)
#     return result.scalars().all()


# ==================== Комнаты ====================

async def get_room_by_name_and_group(session: AsyncSession, name: str, group_id: int) -> Optional[Room]:
    """Получение комнаты по названию и группе"""
    stmt = select(Room).where(
        and_(Room.name == name, Room.id_group == group_id)
    )
    result = await session.execute(stmt)
    return result.scalars().first()


async def get_rooms_by_group(session: AsyncSession, group_id: int) -> List[Room]:
    """Получение всех комнат группы"""
    stmt = select(Room).where(Room.id_group == group_id)
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_room_with_questions(session: AsyncSession, room_id: int) -> Optional[Room]:
    """Получение комнаты со всеми вопросами"""
    stmt = select(Room).options(
        selectinload(Room.questions)
    ).where(Room.id == room_id)
    result = await session.execute(stmt)
    return result.scalars().first()


async def get_or_create_room(session: AsyncSession, name: str, room_key: str, group_id: int) -> Room:
    """Получить или создать комнату"""
    room = await get_room_by_name_and_group(session, name, group_id)
    if not room:
        room = await create_object(session, Room, name=name, room_key=room_key, id_group=group_id)
    return room


# async def get_room_with_full_info(session: AsyncSession, room_id: int) -> Optional[Room]:
#     """Получение комнаты с вопросами и очередью"""
#     stmt = select(Room).options(
#         selectinload(Room.questions),
#         selectinload(Room.queues).joinedload(Queue.student)
#     ).where(Room.id == room_id)
#     result = await session.execute(stmt)
#     return result.scalars().first()


# ==================== Вопросы ====================

async def get_questions_by_room(session: AsyncSession, room_id: int) -> List[Question]:
    """Получение всех вопросов комнаты"""
    stmt = select(Question).where(Question.id_room == room_id)
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_question_with_options(session: AsyncSession, question_id: int) -> Optional[Question]:
    """Получение вопроса с вариантами ответов"""
    stmt = select(Question).where(Question.id == question_id)
    result = await session.execute(stmt)
    return result.scalars().first()


async def get_random_questions_by_room(session: AsyncSession, room_id: int, limit: int = 10) -> List[Question]:
    """Получение случайных вопросов из комнаты"""
    stmt = select(Question).where(
        Question.id_room == room_id
    ).order_by(func.random()).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_questions_count_by_room(session: AsyncSession, room_id: int) -> int:
    """Получение количества вопросов в комнате"""
    stmt = select(func.count(Question.id)).where(Question.id_room == room_id)
    result = await session.execute(stmt)
    return result.scalar() or 0


# ==================== Очередь (Queue) ====================

async def get_queue_by_room_with_students(session: AsyncSession, room_id: int) -> List[Queue]:
    """Получение очереди комнаты с информацией о студентах (сортировка: очки DESC, имя по алфавиту)."""
    # Чтобы сортировать по имени студента, выполняем JOIN со Student
    stmt = (
        select(Queue)
        .options(joinedload(Queue.student))
        .join(Queue.student)
        .where(Queue.id_room == room_id)
        .order_by(desc(Queue.points), Student.name.asc())
    )

    result = await session.execute(stmt)
    return result.scalars().all()


# async def get_active_queue_by_room(session: AsyncSession, room_id: int, limit: int = 10) -> List[Queue]:
#     """Получение активной очереди (первые N позиций)"""
#     stmt = select(Queue).where(
#         Queue.id_room == room_id
#     ).order_by(Queue.position).limit(limit)
#     result = await session.execute(stmt)
#     return result.scalars().all()


async def get_queue_position_by_student_and_room(session: AsyncSession, student_id: int, room_id: int) -> Optional[Queue]:
    """Получение позиции студента в очереди комнаты"""
    stmt = select(Queue).where(
        and_(
            Queue.id_student == student_id,
            Queue.id_room == room_id
        )
    )
    result = await session.execute(stmt)
    return result.scalars().first()


async def get_next_in_queue(session: AsyncSession, room_id: int) -> Optional[Queue]:
    """Получение следующего в очереди (с минимальной позицией)"""
    stmt = select(Queue).where(
        Queue.id_room == room_id
    ).order_by(Queue.position).limit(1)
    result = await session.execute(stmt)
    return result.scalars().first()


async def get_queue_count_students(session: AsyncSession, room_id: int) -> int:
    """Получение количества студентов в очереди комнаты"""
    stmt = select(func.count(Queue.id)).where(Queue.id_room == room_id)
    result = await session.execute(stmt)
    return result.scalar() or 0


async def update_queue_positions(session: AsyncSession, room_id: int):
    """Обновление позиций в очереди после удаления элемента"""
    queue_items = await get_queue_by_room_with_students(session, room_id)

    for index, item in enumerate(queue_items, start=1):
        item.position = index

    await session.commit()


# async def get_leaderboard_by_room(session: AsyncSession, room_id: int, limit: int = 10) -> List[Queue]:
#     """Получение таблицы лидеров комнаты (по очкам)"""
#     stmt = select(Queue).where(
#         Queue.id_room == room_id
#     ).order_by(desc(Queue.points)).limit(limit)
#     result = await session.execute(stmt)
#     return result.scalars().all()


async def get_student_position_in_leaderboard(session: AsyncSession, student_id: int, room_id: int) -> Optional[int]:
    """Получение позиции студента в таблице лидеров"""
    # Создаем подзапрос для ранжирования
    subquery = (
        select(
            Queue.id_student,
            func.rank().over(order_by=desc(Queue.points)).label('rank')
        )
        .where(Queue.id_room == room_id)
        .subquery()
    )

    stmt = select(subquery.c.rank).where(subquery.c.id_student == student_id)
    result = await session.execute(stmt)
    row = result.first()
    return row[0] if row else None


# ==================== Администраторы ====================
async def get_admin_by_tg_id(session: AsyncSession, tg_id: int) -> Optional[Admin]:
    """Получение администратора по Telegram ID"""
    stmt = select(Admin).where(Admin.tg_id == tg_id)
    result = await session.execute(stmt)
    return result.scalars().first()


async def is_admin(session: AsyncSession, tg_id: int) -> bool:
    """Проверка, является ли пользователь администратором"""
    admin = await get_admin_by_tg_id(session, tg_id)
    return admin is not None


async def add_admin(session: AsyncSession, tg_id: int) -> Admin:
    """Добавление нового администратора"""
    admin = Admin(tg_id=tg_id)
    session.add(admin)
    await session.commit()
    await session.refresh(admin)
    return admin


# ==================== Сложные запросы ====================

async def get_student_statistics(session: AsyncSession, student_id: int) -> Dict[str, Any]:
    """Получение статистики студента"""
    # Общее количество очков студента
    stmt = select(func.sum(Queue.points)).where(Queue.id_student == student_id)
    result = await session.execute(stmt)
    total_points = result.scalar() or 0

    # Количество комнат, в которых участвовал
    stmt = select(func.count(Queue.id_room.distinct())
                  ).where(Queue.id_student == student_id)
    result = await session.execute(stmt)
    rooms_count = result.scalar() or 0

    # # Средняя позиция в очереди
    # stmt = select(func.avg(Queue.position)).where(Queue.id_student == student_id)
    # result = await session.execute(stmt)
    # avg_position = result.scalar() or 0

    return {
        'total_points': total_points,
        'rooms_count': rooms_count
        # 'avg_position': avg_position
    }


async def get_room_statistics(session: AsyncSession, room_id: int) -> Dict[str, Any]:
    """Получение статистики комнаты"""
    # Количество вопросов
    questions_count = await get_questions_count_by_room(session, room_id)

    # Количество участников
    stmt = select(func.count(Queue.id_student.distinct())
                  ).where(Queue.id_room == room_id)
    result = await session.execute(stmt)
    participants_count = result.scalar() or 0

    # Максимальное количество очков
    stmt = select(func.max(Queue.points)).where(Queue.id_room == room_id)
    result = await session.execute(stmt)
    max_points = result.scalar() or 0

    # Среднее количество очков
    stmt = select(func.avg(Queue.points)).where(Queue.id_room == room_id)
    result = await session.execute(stmt)
    avg_points = result.scalar() or 0

    return {
        'questions_count': questions_count,
        'participants_count': participants_count,
        'max_points': max_points,
        'avg_points': avg_points
    }


async def search_students(session: AsyncSession, search_term: str, group_id: Optional[int] = None) -> List[Student]:
    """Поиск студентов по имени"""
    stmt = select(Student).where(Student.name.ilike(f"%{search_term}%"))

    if group_id:
        stmt = stmt.where(Student.id_group == group_id)

    stmt = stmt.limit(20)
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_students_without_queue(session: AsyncSession, room_id: int, group_id: int) -> List[Student]:
    """Получение студентов группы, которые еще не в очереди комнаты"""
    # Получаем ID студентов, которые уже в очереди
    subquery = select(Queue.id_student).where(
        Queue.id_room == room_id).subquery()

    # Ищем студентов группы, которых нет в этой очереди
    stmt = select(Student).where(
        and_(
            Student.id_group == group_id,
            ~Student.id.in_(subquery)
        )
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def bulk_create_questions(session: AsyncSession, room_id: int, questions_data: List[Dict]) -> List[Question]:
    """Массовое создание вопросов"""
    questions = []
    for data in questions_data:
        question = Question(
            text=data['text'],
            wrong_answer1=data['wrong_answer1'],
            wrong_answer2=data['wrong_answer2'],
            wrong_answer3=data['wrong_answer3'],
            correct_answer=data['correct_answer'],
            id_room=room_id
        )
        questions.append(question)

    session.add_all(questions)
    await session.commit()

    # Обновляем объекты с ID
    for question in questions:
        await session.refresh(question)

    return questions


async def clear_room_queue(session: AsyncSession, room_id: int) -> int:
    """Очистка очереди комнаты, возвращает количество удаленных записей"""
    stmt = delete(Queue).where(Queue.id_room == room_id)
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount


async def reset_room_points(session: AsyncSession, room_id: int) -> int:
    """Сброс очков у всех участников комнаты"""
    stmt = update(Queue).where(Queue.id_room == room_id).values(points=0)
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount


async def reset_quiz_points(session: AsyncSession, room_id: int) -> int:
    """Сброс баллов у всех участников очереди комнаты в 0 перед началом квиза"""
    stmt = update(Queue).where(Queue.id_room == room_id).values(points=0)
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount


# ==================== Вспомогательные функции ====================

async def check_object_exists(session: AsyncSession, model_class, **filters) -> bool:
    """Проверка существования объекта по фильтрам"""
    stmt = select(model_class).filter_by(**filters).limit(1)
    result = await session.execute(stmt)
    return result.scalars().first() is not None


async def get_or_create(session: AsyncSession, model_class, defaults=None, **kwargs):
    """Получить или создать объект"""
    stmt = select(model_class).filter_by(**kwargs).limit(1)
    result = await session.execute(stmt)
    instance = result.scalars().first()

    if instance:
        return instance, False

    params = kwargs.copy()
    if defaults:
        params.update(defaults)

    instance = model_class(**params)
    session.add(instance)
    await session.commit()
    await session.refresh(instance)
    return instance, True


async def count_objects(session: AsyncSession, model_class, **filters) -> int:
    """Подсчет количества объектов по фильтрам"""
    stmt = select(func.count(model_class.id))

    if filters:
        for key, value in filters.items():
            stmt = stmt.where(getattr(model_class, key) == value)

    result = await session.execute(stmt)
    return result.scalar() or 0


# ==================== Транзакционные операции ====================

async def add_student_to_queue(session: AsyncSession, student_id: int, room_id: int) -> Queue:
    """Добавление студента в очередь комнаты"""
    # Получаем максимальную позицию в очереди
    stmt = select(func.max(Queue.position)).where(Queue.id_room == room_id)
    result = await session.execute(stmt)
    max_position = result.scalar() or 0

    # Создаем новую запись в очереди
    queue = Queue(
        id_student=student_id,
        id_room=room_id,
        position=max_position + 1,
        points=0
    )

    session.add(queue)
    await session.commit()
    await session.refresh(queue)
    return queue


async def remove_student_from_queue(session: AsyncSession, student_id: int, room_id: int) -> bool:
    """Удаление студента из очереди комнаты"""
    queue_item = await get_queue_position_by_student_and_room(session, student_id, room_id)

    if not queue_item:
        return False

    # Удаляем запись из очереди
    await session.delete(queue_item)
    await session.commit()

    # Обновляем позиции оставшихся в очереди
    await update_queue_positions(session, room_id)

    return True


async def increment_student_points(session: AsyncSession, student_id: int, room_id: int, points: int = 1) -> Optional[Queue]:
    """Увеличение очков студента в комнате"""
    queue_item = await get_queue_position_by_student_and_room(session, student_id, room_id)

    if not queue_item:
        return None

    queue_item.points += points
    await session.commit()
    await session.refresh(queue_item)
    return queue_item


async def move_student_in_queue(session: AsyncSession, student_id: int, room_id: int, new_position: int) -> bool:
    """Перемещение студента на новую позицию в очереди"""
    if new_position < 1:
        return False

    queue_item = await get_queue_position_by_student_and_room(session, student_id, room_id)

    if not queue_item:
        return False

    current_position = queue_item.position

    if current_position == new_position:
        return True

    # Если перемещаем вперед (уменьшаем позицию)
    if new_position < current_position:
        # Сдвигаем всех между новой и текущей позицией на +1
        stmt = (
            update(Queue)
            .where(
                and_(
                    Queue.id_room == room_id,
                    Queue.position >= new_position,
                    Queue.position < current_position
                )
            )
            .values(position=Queue.position + 1)
        )
        await session.execute(stmt)

    # Если перемещаем назад (увеличиваем позицию)
    else:
        # Сдвигаем всех между текущей и новой позицией на -1
        stmt = (
            update(Queue)
            .where(
                and_(
                    Queue.id_room == room_id,
                    Queue.position > current_position,
                    Queue.position <= new_position
                )
            )
            .values(position=Queue.position - 1)
        )
        await session.execute(stmt)

    # Устанавливаем новую позицию для студента
    queue_item.position = new_position
    await session.commit()
    return True
