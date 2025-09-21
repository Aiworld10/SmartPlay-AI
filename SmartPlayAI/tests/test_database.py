import pytest
import pytest_asyncio
import uuid
from sqlalchemy import text

from model.models import Player, Question
from model.crud import create_player, get_player_by_name, store_question, load_questions_from_json
from model.schemas import PlayerCreate, QuestionCreate


@pytest.mark.asyncio
async def test_create_player(db_session):
    """Test creating a player in the database."""
    unique_username = f"dbtest_{uuid.uuid4().hex[:8]}"
    player_data = PlayerCreate(name=unique_username)
    player = await create_player(db_session, player_data, "testpassword")

    assert player.name == unique_username
    assert player.password_hash is not None  # Should be hashed
    assert player.id is not None


@pytest.mark.asyncio
async def test_get_player_by_name(db_session):
    """Test retrieving a player by name."""
    unique_username = f"gettest_{uuid.uuid4().hex[:8]}"

    # Create a player
    player_data = PlayerCreate(name=unique_username)
    created_player = await create_player(db_session, player_data, "testpassword")
    await db_session.commit()

    # Retrieve the player
    retrieved_player = await get_player_by_name(db_session, unique_username)

    assert retrieved_player is not None
    assert retrieved_player.name == unique_username
    assert retrieved_player.id == created_player.id


@pytest.mark.asyncio
async def test_get_nonexistent_player(db_session):
    """Test retrieving a player that doesn't exist."""
    non_existent_username = f"nonexistent_{uuid.uuid4().hex[:8]}"
    player = await get_player_by_name(db_session, non_existent_username)

    assert player is None


@pytest.mark.asyncio
async def test_create_questions_bulk(db_session):
    """Test bulk creation of questions."""
    questions_data = [
        QuestionCreate(
            theme="Adventure",
            question_text="You find a mysterious cave. What do you do?"
        ),
        QuestionCreate(
            theme="Mystery",
            question_text="A witness gives conflicting testimony. How do you proceed?"
        )
    ]

    # Create questions using bulk insert
    created_questions = await load_questions_from_json(db_session, questions_data)

    # Verify questions were created
    assert len(created_questions) == 2
    assert created_questions[0].theme == "Adventure"
    assert created_questions[1].theme == "Mystery"

    # Verify in database
    result = await db_session.execute(text("SELECT COUNT(*) FROM questions WHERE theme IN ('Adventure', 'Mystery')"))
    count = result.scalar()
    assert count == 2


@pytest.mark.asyncio
async def test_database_isolation(db_session):
    """Test that each test gets a clean database."""
    # Check that no players exist from previous tests
    result = await db_session.execute(text("SELECT COUNT(*) FROM players"))
    count = result.scalar()
    assert count == 0  # Database should be clean for each test
