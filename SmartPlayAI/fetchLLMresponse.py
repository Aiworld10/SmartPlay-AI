import requests
import json
import os
from dotenv import load_dotenv, set_key
load_dotenv()
url = os.getenv("SERVEO_HOST")
headers = {"Content-Type": "application/json"}


# run serveo_host to run the server and get ready for requests
# SET OLLAMA_HOST=0.0.0.0
# ollama serve --host
# ssh -R 80:localhost:11434 serveo.net
# pass the url to SERVEO_HOST env variable

def evaluate_player_response(question: str, answer: str):
    data = {
        "model": "qwen3:14b",
        "messages": [
            {
                "role": "system",
                "content": (
                    """You are the game judge in SmartPlay AI. Evaluate the player's response using the exact structure and wording below. Write exactly 4 sentences in one concise paragraph, then output a JSON object on a new line with fields "verdict" (GOOD or BAD) and "score" (0–5). Use only the adjectives: clear / partially clear / unclear, adaptable / partially adaptable / not adaptable, emotionally attuned / partially attuned / not attuned. Do not introduce synonyms. Do not change the sentence templates.
                        Sentence 1 (Clarity): "Evaluation: The response is {clear|partially clear|unclear} in addressing the scenario and states a rationale."
                        Sentence 2 (Adaptability): "It is {adaptable|partially adaptable|not adaptable} in managing constraints and adjusting to the scenario's pressure."
                        Sentence 3 (Emotional intelligence): "It is {emotionally attuned|partially attuned|not attuned} to stakeholders by acknowledging concerns and maintaining a constructive tone."
                        Sentence 4 (Consequence): "As a result, the likely consequence is {positive|mixed|negative} for outcomes and relationships."
                        Rubric → verdict/score (apply exactly):
                        - If clarity = clear AND adaptability = adaptable AND EI = emotionally attuned → verdict=GOOD, score=4–5 (use 5 if consequences=positive, else 4).
                        - If at least two dimensions are "partial" and none are "not/unclear" → verdict=GOOD, score=3.
                        - If one dimension is "not/unclear" and the others are at least partial → verdict=BAD, score=2.
                        - If two or more dimensions are "not/unclear" → verdict=BAD, score=0–1 (use 1 if consequences=mixed, else 0).
                        Output the JSON immediately after the paragraph, starting with "{" and containing only "verdict" and "score".
                        Example (format only, do not rephrase):
                        Evaluation: The response is partially clear in addressing the scenario and states a rationale. It is partially adaptable in managing constraints and adjusting to the scenario's pressure. It is partially attuned to stakeholders by acknowledging concerns and maintaining a constructive tone. As a result, the likely consequence is mixed for outcomes and relationships.
                        {"verdict":"GOOD","score":3}"""
                )
            },
            {
                "role": "user",
                "content": f"Question: {question}\nPlayer Response: {answer}"
            }
        ],
        "temperature": 0,
        "stream": False,
        "think": False,
        "seed": 42,
        "top_p": 1.0,
        "top_k": 1,
    }

    try:
        response = requests.post(url, headers=headers,
                                 data=json.dumps(data), timeout=10)

        if not response.ok:
            raise RuntimeError(
                f"API Error {response.status_code}: {response.text}")

        body = response.json()
        content = body.get("message", {}).get("content", "").strip()

        lines = content.split("\n")
        json_line = lines[-1].strip()
        evaluation_text = "\n".join(lines[:-1]).strip()

        try:
            result = json.loads(json_line)
        except json.JSONDecodeError:
            result = {"verdict": None, "score": None}

        return evaluation_text, result
    except Exception as e:
        print(f"[Fallback] Using default evaluation due to error: {e}")
        return "", {"verdict": "BAD", "score": 1}


# -------------------------------
# # Example usage
# if __name__ == "__main__":
#     question = "Work situation: Your written reports are accurate but full of typos and formatting mistakes. How do you handle this?"
#     answer = "I would still submit it because ti didnt matters. anyway"

#     evaluation, result = evaluate_player_response(question, answer)
#     print("Evaluation:", evaluation)
#     print("Verdict:", result["verdict"])
#     print("Score:", result["score"])
