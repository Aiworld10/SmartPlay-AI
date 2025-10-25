
from difflib import SequenceMatcher  # for text similarity comparison
import pytest
import uuid
from sqlalchemy import text

from fetchLLMresponse import evaluate_player_response
from model.crud import create_player, get_player_by_name, get_random_questions_by_theme, store_question, load_questions_from_json, store_response, reset_user_responses
from model.schemas import PlayerCreate, QuestionCreate
from model import schemas


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
    username = f"gettest_{uuid.uuid4().hex[:8]}"

    # Create a player
    player_data = PlayerCreate(name=username)
    created_player = await create_player(db_session, player_data, "testpassword")
    await db_session.commit()

    # Retrieve the player
    fetched_player = await get_player_by_name(db_session, username)

    assert fetched_player is not None
    assert fetched_player.name == username
    assert fetched_player.id == created_player.id


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
            theme="survival",
            question_text="You find a mysterious cave. What do you do?"
        ),
        QuestionCreate(
            theme="moral",
            question_text="A stranger asks for help. Do you assist them?"
        )
    ]

    # Create questions using bulk insert
    created_questions = await load_questions_from_json(db_session, questions_data)

    # Verify questions were created
    assert len(created_questions) == 2
    assert created_questions[0].theme == "survival"
    assert created_questions[1].theme == "moral"

    # Verify in database
    result = await db_session.execute(text("SELECT COUNT(*) FROM questions WHERE theme IN ('survival', 'moral')"))
    count = result.scalar()
    assert count == 2


@pytest.mark.asyncio
async def test_database_isolation(db_session):
    """Test that each test gets a clean database."""
    # Check that no players exist from previous tests
    result = await db_session.execute(text("SELECT COUNT(*) FROM players"))
    count = result.scalar()
    assert count == 0  # Database should be clean for each test


@pytest.mark.asyncio
async def test_get_random_questions_by_theme(db_session):
    """Test retrieving random questions by theme."""
    theme = "survival"
    questions_data = [
        QuestionCreate(theme=theme, question_text=f"Survival question {i}") for i in range(10)
    ]

    # Insert questions
    await load_questions_from_json(db_session, questions_data)

    # Retrieve random questions
    random_questions = await get_random_questions_by_theme(db_session, theme, limit=5)

    assert len(random_questions) == 5
    for question in random_questions:
        assert question.theme == theme


@pytest.mark.asyncio
async def test_evaluate_response_with_verdict(db_session):
    """Test evaluate the resposne from LLM with a verdict and score"""
    question_data = QuestionCreate(
        theme="moral",
        question_text="You find a wallet with $500 cash and no ID. What do you do?"
    )

    # Store the question
    stored_question = await store_question(db_session, question_data)

    # Create a response from user to pass to LLM using fetchLLMResponse.py
    user_response = "I would take the cash and leave the wallet where I found it."
    llm_response = evaluate_player_response(
        user_response, stored_question.question_text)
    verdict = llm_response[1]['verdict']
    score = llm_response[1]["score"]
    assert verdict in ["GOOD", "BAD"]
    assert score in [0, 1, 2, 3, 4, 5]


@pytest.mark.asyncio
async def test_update_player_score(db_session):
    """Test updating a player's score."""
    username = f"scoretest_{uuid.uuid4().hex[:8]}"

    # Create a player
    player_data = PlayerCreate(name=username)
    player = await create_player(db_session, player_data, "testpassword")
    await db_session.commit()

    # Update the player's score
    new_score = 10
    player.score = new_score
    db_session.add(player)
    await db_session.commit()
    await db_session.refresh(player)

    # Fetch the player again to verify the score update
    updated_player = await get_player_by_name(db_session, username)

    assert updated_player.score == new_score


@pytest.mark.asyncio
async def test_get_leaderboard(db_session):
    """Test retrieving the leaderboard."""
    # Create multiple players with different scores
    players_data = [
        PlayerCreate(name=f"leader_{i}") for i in range(5)
    ]
    for i, pdata in enumerate(players_data):
        player = await create_player(db_session, pdata, "testpassword")
        player.score = i * 10  # Assign scores 0, 10, 20, 30, 40
        db_session.add(player)
    await db_session.commit()

    # Retrieve top 5 players by score
    result = await db_session.execute(
        text("SELECT * FROM players ORDER BY score DESC LIMIT 5")
    )
    top_players = result.fetchall()

    assert len(top_players) == 5
    assert top_players[0].score >= top_players[1].score >= top_players[2].score >= top_players[3].score >= top_players[4].score


@pytest.mark.asyncio
async def test_exclude_answered(db_session):
    """Test retrieving random questions by theme excluding those already answered by the player."""
    theme = "survival"
    player_id = 1  # Simulate a player with ID 1

    # Create questions
    questions_data = [
        QuestionCreate(theme=theme, question_text=f"Survival question {i}") for i in range(10)
    ]
    created_questions = await load_questions_from_json(db_session, questions_data)

    # use store_response() to simulate that player has answered first 5 questions
    for question in created_questions:
        response = schemas.ResponseCreate(
            question_id=question.id, player_id=player_id, response_text="Sample answer", score=3)
        await store_response(db_session, response)
    await db_session.commit()
    # Retrieve random questions excluding those already answered
    random_questions = await get_random_questions_by_theme(db_session, theme, limit=5, player_id=player_id)
    assert len(random_questions) == 0  # All questions have been answered


@pytest.mark.asyncio
async def test_reset_answered_questions(db_session):
    """Test resetting answered questions for a player."""
    theme = "theme"
    player_id = 1  # Simulate a player with ID 1

    # Create questions
    questions_data = [
        QuestionCreate(theme=theme, question_text=f"Theme question {i}") for i in range(5)
    ]
    created_questions = await load_questions_from_json(db_session, questions_data)

    # Simulate that player has answered all questions
    for question in created_questions:
        response = schemas.ResponseCreate(
            question_id=question.id, player_id=player_id, response_text="Sample answer", score=3)
        await store_response(db_session, response)
    await db_session.commit()

    # Verify no questions are returned when fetching random questions
    random_questions_before_reset = await get_random_questions_by_theme(db_session, theme, limit=5, player_id=player_id)
    assert len(random_questions_before_reset) == 0

    # Reset answered questions for the player
    await reset_user_responses(db_session, player_id)
    await db_session.commit()
    # Verify questions are now available after reset
    random_questions_after_reset = await get_random_questions_by_theme(db_session, theme, limit=5, player_id=player_id)
    # Should retrieve questions now
    assert len(random_questions_after_reset) > 0


@pytest.mark.asyncio
async def test_store_and_retrieve_llm_feedback(db_session):
    """Test storing and retrieving LLM feedback for a response."""
    # Create player and question
    player_data = PlayerCreate(name=f"feedback_{uuid.uuid4().hex[:8]}")
    player = await create_player(db_session, player_data, "testpassword")

    question_data = QuestionCreate(
        theme="ethics",
        question_text="Should AI be allowed to make moral decisions?"
    )
    question = await store_question(db_session, question_data)
    await db_session.commit()

    # Store a response
    response_data = schemas.ResponseCreate(
        player_id=player.id,
        question_id=question.id,
        response_text="AI can assist, but humans should have the final say.",
        score=4
    )
    response = await store_response(db_session, response_data)
    await db_session.commit()

    # Add LLM feedback to this response
    feedback_text = "Good reasoning, aligns with ethical responsibility."
    response.llm_feedback = feedback_text
    await db_session.commit()
    await db_session.refresh(response)

    # Verify feedback was stored
    assert response.llm_feedback == feedback_text

    # Fetch directly from DB to double-check persistence
    result = await db_session.execute(
        text("SELECT llm_feedback FROM responses WHERE player_id=:pid AND question_id=:qid"),
        {"pid": player.id, "qid": question.id}
    )
    stored_feedback = result.scalar_one()
    assert stored_feedback == feedback_text


@pytest.mark.asyncio
async def test_toggle_like_dislike_response(db_session):
    """Test updating the liked status on a response without affecting the player's score."""
    # Create player and question
    player_data = PlayerCreate(name=f"like_{uuid.uuid4().hex[:8]}")
    player = await create_player(db_session, player_data, "testpassword")

    question_data = QuestionCreate(
        theme="social",
        question_text="Would you share your last piece of food with a friend?"
    )
    question = await store_question(db_session, question_data)
    await db_session.commit()

    # Store response
    response_data = schemas.ResponseCreate(
        player_id=player.id,
        question_id=question.id,
        response_text="Yes, sharing is caring.",
        score=5
    )
    response = await store_response(db_session, response_data)
    await db_session.commit()
    await db_session.refresh(player)
    initial_score = player.score

    # Player likes the LLM feedback
    response.liked = True
    await db_session.commit()
    await db_session.refresh(response)

    # Player changes their mind — dislikes
    response.liked = False
    await db_session.commit()
    await db_session.refresh(response)
    await db_session.refresh(player)

    assert response.liked is False
    # Ensure the player's score remains unchanged
    assert player.score == initial_score


def similar(a: str, b: str) -> float:
    """Compute similarity ratio between two strings."""
    return SequenceMatcher(None, a, b).ratio()


@pytest.mark.asyncio
async def test_fetch_llm_response_consistency():
    """Test that the LLM response evaluation is consistent across repeated calls."""
    question_text = "Is it ethical to use AI in warfare?"
    player_response = "AI should not be used in warfare as it can lead to unintended consequences."

    first_eval = evaluate_player_response(player_response, question_text)
    # debug print(first_eval)
    print(first_eval)
    second_eval = evaluate_player_response(player_response, question_text)
    print(second_eval)
    # Compare structure
    first_text, first_meta = first_eval
    second_text, second_meta = second_eval

    # Check verdict and score are the same (deterministic numeric logic)
    assert first_meta["verdict"] == second_meta["verdict"], "Verdicts differ between runs"
    assert first_meta["score"] == second_meta["score"], "Scores differ between runs"

    # Check textual similarity — small LLM phrasing differences allowed
    sim = similar(first_text, second_text)
    assert sim > 0.65, f"LLM feedback text varied too much (similarity={sim:.2f})"
