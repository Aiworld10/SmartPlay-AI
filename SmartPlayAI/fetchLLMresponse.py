import requests
import json
import os
from dotenv import load_dotenv
load_dotenv()
url = os.getenv("SERVEO_HOST")
headers = {"Content-Type": "application/json"}


def evaluate_player_response(question: str, answer: str):
    data = {
        "model": "qwen3:14b",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are the game judge in SmartPlay AI. A player is given a scenario and responds under pressure. "
                    "Write your evaluation as one concise paragraph (no more than 5 sentences) that explains the consequences "
                    "of the player's choice and whether it shows clarity, adaptability, and emotional intelligence. "
                    "At the end, output a separate JSON object on a new line with two fields: 'verdict' (GOOD or BAD) and 'score' (1–5). "
                    "Example format:\nEvaluation: <your paragraph here>\n{\"verdict\": \"BAD\", \"score\": 1}"
                )
            },
            {"role": "user", "content": question},
            {"role": "user", "content": f"Player Response: {answer}"}
        ],
        "stream": False,
        "think": False,
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if not response.ok:
        raise RuntimeError(
            f"API Error {response.status_code}: {response.text}")

    body = response.json()
    content = body.get("message", {}).get("content", "").strip()

    # split evaluation + JSON
    lines = content.split("\n")
    json_line = lines[-1].strip()
    evaluation_text = "\n".join(lines[:-1]).strip()

    try:
        result = json.loads(json_line)
    except json.JSONDecodeError:
        result = {"verdict": None, "score": None}

    return evaluation_text, result


# -------------------------------
# # Example usage
# if __name__ == "__main__":
#     question = "Work situation: Your written reports are accurate but full of typos and formatting mistakes. How do you handle this?"
#     answer = "I would still submit it because ti didnt matters. anyway"

#     evaluation, result = evaluate_player_response(question, answer)
#     print("Evaluation:", evaluation)
#     print("Verdict:", result["verdict"])
#     print("Score:", result["score"])
