import requests
import json
import os
import re
from dotenv import load_dotenv, set_key

load_dotenv()
url = os.getenv("SERVEO_HOST")
headers = {"Content-Type": "application/json"}

# Canonical scoring rules shared across all themes
BASE_RULES = """
Rubric → verdict/score (apply exactly):
- If clarity = clear AND adaptability = adaptable AND EI = emotionally attuned → verdict=GOOD, score=4–5 (use 5 if consequences=positive, else 4).
- If at least two dimensions are "partial" and none are "not/unclear" → verdict=GOOD, score=3.
- If one dimension is "not/unclear" and the others are at least partial → verdict=BAD, score=2.
- If two or more dimensions are "not/unclear" → verdict=BAD, score=0–1 (use 1 if consequences=mixed, else 0).

Formatting rules:
- Write exactly four sentences of analysis, one each for clarity, adaptability, emotional intelligence, and consequence.
- You may vary tone and sentence structure; do not sound formulaic.
- After the paragraph, output the JSON with keys "verdict" and "score".
Example (format only):
"What you should have done... (4 sentences)"
{"verdict":"GOOD","score":3}
"""


def _build_system_prompt(theme: str) -> str:
    theme = (theme or "").lower()

    # Shared context
    voice_context = (
        "You are a narrator or coach who adapts tone to each scenario. "
        "You speak naturally, with emotional awareness and narrative flow. "
        "Your task: describe how the scene unfolds, then give 4 reflective sentences "
        "covering clarity, adaptability, emotional awareness, and consequence — "
        "without sounding repetitive or robotic. Each theme has its own personality. "
        "Before analyzing, quickly judge if the player's response is meaningful, relevant, and complete. "
        "If it is empty, nonsensical, or one-word with no context, treat all dimensions as 'not/unclear' and assign score=0 with verdict=BAD. "
    )

    # Theme-specific personalities
    if theme == "survival":
        personality = (
            "Personality Signature: You are a cinematic survival narrator — poetic yet grounded. "
            "You describe sensory detail vividly and teach survival through hindsight, like fate speaking after the storm."
        )
        rubric = """
- Assess clarity: did the player truly understand the danger and respond coherently, or act blindly?
- Reflect on adaptability: did they use their environment, tools, or instincts to survive, or freeze under pressure?
- Evaluate instinct: did they trust fear, stay calm, and act with control, or let panic rule them?
- Conclude with consequence: describe how their choices sealed or could have changed their fate.
"""
        preface = (
            "Describe in 3–4 sentences how the player's ordeal unfolds — the sounds, heat, or silence — "
            "and how their choices lead to tragedy or narrow escape. Then reflect using the four angles below. "
            "Be vivid, human, and instructive, like the voice of survival itself."
        )

    elif theme == "work":
        personality = (
            "Personality Signature: You are a calm leadership coach — clear, empathetic, and constructive. "
            "You analyze communication, teamwork, and reasoning like mentoring an employee after a meeting."
        )
        rubric = """
- Clarity: Did the person recognize and address the real workplace issue, or misread it? Point out what was missed or misunderstood.
- Adaptability: Did they listen, seek feedback, or propose a practical fix? Offer what a more proactive step could look like.
- Emotional intelligence: Did they communicate with composure, respect, and accountability? Suggest how tone could improve.
- Consequence: Reflect on how better choices might have affected teamwork, trust, or credibility.
"""
        preface = (
            "Describe briefly how the workplace situation unfolded — what the person said or did, and how others reacted. "
            "Then provide balanced reflection using the four aspects below. "
            "Write as if giving real coaching feedback, natural and precise."
        )

    elif theme == "interview":
        personality = (
            "Personality Signature: You are a professional interviewer — analytical, composed, and encouraging. "
            "You care about clarity, adaptability, and self-awareness in the candidate’s responses."
        )
        rubric = """
- Clarity: Did the candidate actually answer the question and highlight relevant experience, or drift off-topic? Explain clearly.
- Adaptability: Did they adjust tone or examples, or show flexibility when unsure? Offer how to improve delivery or framing.
- Composure: Did they stay calm, confident, and authentic? Reflect on their tone and presence.
- Consequence: Describe how a stronger answer could change hiring impressions.
"""
        preface = (
            "Describe how the interview unfolds — the tone, pacing, and interviewer’s impression. "
            "Then reflect on what the candidate could improve in structure, confidence, and adaptability."
        )

    elif theme == "social":
        personality = (
            "Personality Signature: You are an empathetic social observer — insightful and warm. "
            "You understand human emotion, tone, and timing. You reflect gently but truthfully."
        )
        rubric = """
- Clarity: Did the person express themselves clearly, or let emotions cloud communication? Point out why.
- Adaptability: Did they listen, pause, or adjust words to defuse tension? Suggest how they could have responded better.
- Empathy: Did they recognize how the other person felt, or miss emotional cues? Show what empathy might have changed.
- Impact: Explain how a different approach could affect trust, connection, or harmony.
"""
        preface = (
            "Describe the emotional dynamic of the interaction — how it began, escalated, or softened. "
            "Then reflect on how the player could have improved empathy and connection using the four dimensions below."
        )

    else:
        personality = (
            "Personality Signature: You are a neutral observer, offering practical and fair evaluation of general behavior."
        )
        rubric = """
- Clarity: Did the person understand and address the situation logically?
- Adaptability: Did they adjust effectively to change or challenge?
- Emotional awareness: Did they stay composed and considerate?
- Consequence: Reflect briefly on likely outcomes based on their behavior.
"""
        preface = (
            "Give a concise, balanced reflection of the situation and improvements possible."
        )

    return f"{voice_context}\n\n{personality}\n\n{preface}\n\nUse these guiding ideas:\n{rubric}\n\nAdd subtle variety in phrasing and rhythm so every reflection feels human and situational.\n{BASE_RULES}"


def _extract_json_and_text(content: str):
    s = content.strip()
    s = re.sub(r"```json\s*", "", s, flags=re.IGNORECASE)
    s = s.replace("```", "")

    start = s.rfind("{")
    result = {"verdict": None, "score": None}
    evaluation_text = s

    if start != -1:
        end = s.find("}", start)
        while end != -1:
            candidate = s[start:end+1]
            try:
                parsed = json.loads(candidate)
                evaluation_text = s[:start].strip()
                result = parsed
                break
            except json.JSONDecodeError:
                end = s.find("}", end + 1)

    verdict = (result.get("verdict") or "").upper().strip()
    verdict = "GOOD" if verdict == "GOOD" else (
        "BAD" if verdict == "BAD" else None)

    score = result.get("score")
    try:
        score = int(round(float(score)))
    except Exception:
        score = None
    if score is not None:
        score = max(0, min(5, score))

    return evaluation_text, {"verdict": verdict, "score": score}


def evaluate_player_response(question: str, answer: str, theme: str = "", **kwargs):
    system_prompt = _build_system_prompt(theme)

    data = {
        "model": "qwen3:14b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Theme: {theme}\nQuestion: {question}\nPlayer Response: {answer}"},
        ],
        "temperature": 0.6,   # slightly creative for natural tone
        "stream": False,
        "think": False,
        "seed": 42,
        "top_p": 0.9,
        "top_k": 5,
    }

    try:
        response = requests.post(url, headers=headers,
                                 data=json.dumps(data), timeout=20)
        if not response.ok:
            raise RuntimeError(
                f"API Error {response.status_code}: {response.text}")

        body = response.json()
        content = body.get("message", {}).get("content", "").strip()

        evaluation_text, result = _extract_json_and_text(content)

        if result["verdict"] not in ("GOOD", "BAD") or result["score"] is None:
            result = {"verdict": "BAD", "score": 0}

        return evaluation_text, result

    except Exception as e:
        print(f"[Fallback] Using default evaluation due to error: {e}")
        return "", {"verdict": "BAD", "score": 0}
