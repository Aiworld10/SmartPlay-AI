from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from . import models, schemas
from typing import List
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
#######################################################
# Players CRUD
#######################################################


async def get_player(db: AsyncSession, player_id: int):
    """
    Retrieve a Player instance by primary key.

    Args:
        db (AsyncSession): Async SQLAlchemy database session.
        player_id (int): Unique identifier of the Player.

    Returns:
        Player | None: The Player object if found, otherwise None.
    """
    result = await db.get(models.Player, player_id)
    return result


async def get_player_by_name(db: AsyncSession, name: str):
    result = await db.execute(
        select(models.Player).where(models.Player.name == name)
    )
    return result.scalar_one_or_none()


async def create_player(db: AsyncSession, player: schemas.PlayerCreate, plain_password: str):
    """
    Create a new Player instance.

    Args:
        db (AsyncSession): Async SQLAlchemy database session.
        player (PlayerCreate): Pydantic model containing player creation data.

    Returns:
        Player: The newly created Player object.
    """
    hashed_password = pwd_context.hash(plain_password)
    user = models.Player(
        name=player.name, score=player.score, password_hash=hashed_password)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

######################################################
# Questions CRUD
######################################################


async def get_question(db: AsyncSession, question_id: int):
    """
    Retrieve a Question instance by primary key.

    Args:
        db (AsyncSession): Async SQLAlchemy database session.
        question_id (int): Unique identifier of the Question.

    Returns:
        Question | None: The Question object if found, otherwise None.
    """
    result = await db.get(models.Question, question_id)
    return result


async def get_question_by_id(db: AsyncSession, question_id: int):
    return await db.get(models.Question, question_id)


async def get_random_questions_by_theme(db: AsyncSession, theme: str, limit: int = 5):
    result = await db.execute(
        select(models.Question)
        .where(models.Question.theme == theme)
        .order_by(func.random())
        .limit(limit)
    )
    return result.scalars().all()


async def store_question(db: AsyncSession, question: schemas.QuestionCreate):
    """
    Store a new Question instance in the database.

    Args:
        db (AsyncSession): Async SQLAlchemy database session.
        question (QuestionCreate): Pydantic model containing question creation data.

    Returns:
        Question: The newly created Question object.
    """
    db_question = models.Question(
        theme=question.theme, question_text=question.question_text)
    db.add(db_question)
    await db.commit()
    await db.refresh(db_question)
    return db_question


async def load_questions_from_json(
    db: AsyncSession, questions: List[schemas.QuestionCreate]
) -> List[models.Question]:
    """
    Bulk insert Question instances from a list of QuestionCreate schemas.

    Args:
        db (AsyncSession): Async SQLAlchemy database session.
        questions (list[QuestionCreate]): List of Pydantic models or dicts containing question data.

    Returns:
        list[Question]: The newly created Question objects.
    """
    db_questions = [
        models.Question(theme=q.theme, question_text=q.question_text)
        for q in questions
    ]

    db.add_all(db_questions)
    await db.commit()
    return db_questions


async def delete_all_questions(db: AsyncSession) -> int:
    """
    Delete all Question instances from the database.

    Args:
        db (AsyncSession): Async SQLAlchemy database session.

    Returns:
        int: The number of questions deleted.
    """
    from sqlalchemy import delete

    # Execute delete statement for all questions
    result = await db.execute(delete(models.Question))
    deleted_count = result.rowcount
    await db.commit()

    return deleted_count

######################################################
# Responses CRUD
######################################################


async def store_response(db: AsyncSession, response: schemas.ResponseCreate):
    """
    Store a new Response instance in the database.

    Args:
        db (AsyncSession): Async SQLAlchemy database session.
        response (ResponseCreate): Pydantic model containing response creation data.

    Returns:
        Response: The newly created Response object.
    """
    db_response = models.Response(
        player_id=response.player_id,
        question_id=response.question_id,
        response_text=response.response_text,
        score=response.score
    )
    db.add(db_response)
    await db.commit()
    await db.refresh(db_response)
    return db_response


async def get_responses_by_player(db: AsyncSession, player_id: int):
    """
    Retrieve all Response instances associated with a specific player.

    Args:
        db (AsyncSession): Async SQLAlchemy database session.
        player_id (int): Unique identifier of the Player.

    Returns:
        list[Response]: A list of Response objects associated with the player.
    """
    result = await db.execute(
        select(models.Response).where(models.Response.player_id == player_id)
    )
    return result.scalars().all()
