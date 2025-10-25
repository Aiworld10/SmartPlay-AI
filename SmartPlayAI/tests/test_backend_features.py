import uuid

import pytest
from fastapi.testclient import TestClient


def _register_and_login(client: TestClient) -> str:
    """Register and login a user, returning the username."""
    username = f"user_{uuid.uuid4().hex[:8]}"
    client.post(
        "/auth/register",
        data={
            "username": username,
            "password1": "testpassword",
            "password2": "testpassword",
        },
    )
    client.post(
        "/auth/login",
        data={
            "username": username,
            "password": "testpassword",
        },
    )
    return username


def _create_question(client: TestClient, theme: str, text: str) -> dict:
    """Helper to create a question via the API."""
    response = client.post(
        "/questions/create",
        data={"theme": theme, "question_text": text},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    response.raise_for_status()
    return response.json()


# @pytest.mark.parametrize("second_attempt_same_player", [True, False])
# def test_answer_question_caches_llm_feedback(client: TestClient, monkeypatch, second_attempt_same_player: bool):
#     """Ensure identical question/answer pairs reuse stored LLM feedback."""

#     call_count = {"count": 0}

#     def fake_evaluate(question: str, answer: str):
#         call_count["count"] += 1
#         return (
#             "Mock evaluation explaining strengths and weaknesses.",
#             {"verdict": "GOOD", "score": 5},
#         )

#     monkeypatch.setattr("router.responses.evaluate_answer", fake_evaluate)

#     # First user registers and answers.
#     first_username = _register_and_login(client)
#     question = _create_question(client, "work", "Your team misses a critical deadline. What do you tell your manager?")
#     payload = {
#         "question_id": str(question["id"]),
#         "question_text": question["question_text"],
#         "response_text": "I would own the mistake and present a recovery plan.",
#     }

#     first_response = client.post("/responses/answer", data=payload)
#     assert first_response.status_code == 200
#     data = first_response.json()
#     assert data["score"] == 5
#     assert data["evaluation"].startswith("Mock evaluation")
#     assert call_count["count"] == 1

#     # Optionally simulate a second user hitting the same question/answer combo
#     if not second_attempt_same_player:
#         # Need a fresh session to avoid cookie collision
#         with TestClient(client.app) as second_client:
#             _register_and_login(second_client)
#             second_payload = payload.copy()
#             second_response = second_client.post("/responses/answer", data=second_payload)
#     else:
#         second_response = client.post("/responses/answer", data=payload)

#     assert second_response.status_code == 200
#     second_data = second_response.json()
#     # Cached response should avoid another LLM invocation
#     assert call_count["count"] == 1
#     assert second_data["score"] == 5
#     assert second_data["evaluation"].startswith("Mock evaluation")


def test_like_dislike_feedback_requires_owner(client: TestClient, monkeypatch):
    """Only the response owner can update like/dislike status."""
    monkeypatch.setattr(
        "router.responses.evaluate_answer",
        lambda question, answer: (
            "Evaluation body", {"verdict": "GOOD", "score": 4}),
    )

    _register_and_login(client)
    question = _create_question(
        client, "survival", "You are stranded overnight without shelter. What is your plan?")
    payload = {
        "question_id": str(question["id"]),
        "question_text": question["question_text"],
        "response_text": "I build a shelter from nearby branches and leaves.",
    }
    answer_response = client.post("/responses/answer", data=payload)
    assert answer_response.status_code == 200
    response_data = answer_response.json()
    player_id = response_data["db_response"]["player_id"]
    question_id = response_data["db_response"]["question_id"]

    like_response = client.post(
        f"/responses/{player_id}/{question_id}/feedback",
        json={"liked": True},
    )
    assert like_response.status_code == 200
    assert like_response.json()["liked"] is True

    # Switch to a different user
    with TestClient(client.app) as other_client:
        _register_and_login(other_client)
        forbidden = other_client.post(
            f"/responses/{player_id}/{question_id}/feedback",
            json={"liked": False},
        )
    assert forbidden.status_code == 403


def test_list_response_feedback_filter(client: TestClient, monkeypatch):
    """Feedback endpoint should filter by liked status."""
    monkeypatch.setattr(
        "router.responses.evaluate_answer",
        lambda question, answer: (
            "Quick eval", {"verdict": "BAD", "score": 2}),
    )

    _register_and_login(client)
    question = _create_question(
        client, "interview", "Describe a time you overcame a conflict.")
    payload = {
        "question_id": str(question["id"]),
        "question_text": question["question_text"],
        "response_text": "I facilitated a discussion to ensure everyone felt heard.",
    }
    answer_response = client.post("/responses/answer", data=payload)
    resp_data = answer_response.json()
    player_id = resp_data["db_response"]["player_id"]
    question_id = resp_data["db_response"]["question_id"]

    client.post(
        f"/responses/{player_id}/{question_id}/feedback", json={"liked": False})

    liked_items = client.get("/responses/feedback", params={"liked": "true"})
    assert liked_items.status_code == 200
    assert liked_items.json() == []

    disliked_items = client.get(
        "/responses/feedback", params={"liked": "false"})
    assert disliked_items.status_code == 200
    assert len(disliked_items.json()) == 1
    assert disliked_items.json()[0]["liked"] is False


def test_leaderboard_details_returns_data(client: TestClient, monkeypatch):
    """Leaderboard details endpoint should include response metadata."""
    monkeypatch.setattr(
        "router.responses.evaluate_answer",
        lambda question, answer: (
            "Detailed eval", {"verdict": "GOOD", "score": 3}),
    )

    _register_and_login(client)
    question = _create_question(
        client, "survival", "You need water but only find murky puddles. What now?")
    payload = {
        "question_id": str(question["id"]),
        "question_text": question["question_text"],
        "response_text": "I boil the water to purify it before drinking.",
    }
    client.post("/responses/answer", data=payload)

    details_response = client.get(
        "/leaderboard/details", params={"theme": "survival"})
    assert details_response.status_code == 200
    details = details_response.json()
    assert len(details) == 1
    entry = details[0]
    assert entry["theme"] == "survival"
    assert entry["question_text"] == question["question_text"]
    assert entry["response_text"] == payload["response_text"]
    assert entry["score"] == 3
