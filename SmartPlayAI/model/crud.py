from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
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


async def get_player_by_name(db: AsyncSession, name: str) -> models.Player | None:
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
        name=player.name, password_hash=hashed_password, created_at=func.now()
    )
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


async def get_random_questions_by_theme(db: AsyncSession, theme: str, limit:
                                        int = 5, player_id: int = 0):
    """
    Retrieve a list of random Question instances filtered by theme.
    player will only see those question once after they submit an answer.
    they will have the option to ignore that and go to next

    Args:
        db (AsyncSession): Async SQLAlchemy database session.
        theme (str): Theme to filter questions by.
        limit (int): Maximum number of questions to retrieve.
    """
    stmt = (
        select(models.Question)
        .where(
            models.Question.theme == theme,
            # NOT EXISTS subquery to exclude questions already answered by the player ~ symbol is NOT
            ~select(1)
            .where(
                models.Response.player_id == player_id,
                models.Response.question_id == models.Question.id,
            )
            .select_from(models.Response)
            .exists()
            if player_id is not None else True  # no filter if no player_id
        )
        .order_by(func.random())
        .limit(limit)
    )
    result = await db.execute(stmt)
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


async def reset_player_scores(db: AsyncSession, player_id: int):
    """Reset a player's score to 0."""
    if not player_id:
        return None
    else:
        player_id = int(player_id)
    result = await db.execute(
        select(models.Player).where(models.Player.id == player_id)
    )
    player = result.scalar_one_or_none()

    if player:
        player.score = 0  # column[int] = int is allowed
        await db.commit()
        await db.refresh(player)

    return player


async def reset_user_responses(db: AsyncSession, player_id: int) -> int:
    """Delete all responses for a specific player."""
    if not player_id:
        return 0
    else:
        player_id = int(player_id)
    result = await db.execute(
        select(models.Response).where(models.Response.player_id == player_id)
    )
    responses = result.scalars().all()

    for response in responses:
        await db.delete(response)

    deleted_count = len(responses)
    await db.commit()

    return deleted_count


async def get_leaderboard(db: AsyncSession, theme: str | None = None, limit: int = 10):
    """
    Get leaderboard data, optionally filtered by theme.

    Args:
        db (AsyncSession): Async SQLAlchemy database session.
        theme (str, optional): Theme to filter by.
        limit (int): Maximum number of players to return.

    Returns:
        list: List of player leaderboard data.
    """
    # Base query joining players with their responses
    query = (
        select(
            models.Player.id,
            models.Player.name,
            func.coalesce(func.sum(models.Response.score), 0).label('score'),
            func.count(models.Response.player_id).label('games_played'),
            func.coalesce(func.avg(models.Response.score),
                          0).label('average_score')
        )
        .select_from(models.Player)
        .outerjoin(models.Response, models.Player.id == models.Response.player_id)
    )

    # If theme is specified, join with questions to filter by theme
    if theme:
        query = (
            query
            .outerjoin(models.Question, models.Response.question_id == models.Question.id)
            .where(models.Question.theme == theme)
        )

    # Group by player and order by score descending
    query = (
        query
        .group_by(models.Player.id, models.Player.name)
        .order_by(func.coalesce(func.sum(models.Response.score), 0).desc())
        .limit(limit)
    )

    result = await db.execute(query)
    rows = result.fetchall()

    # Convert to list of dictionaries
    leaderboard = []
    for row in rows:
        leaderboard.append({
            'id': row.id,
            'name': row.name,
            'score': int(row.score),
            'games_played': int(row.games_played),
            'average_score': float(row.average_score)
        })

    return leaderboard
