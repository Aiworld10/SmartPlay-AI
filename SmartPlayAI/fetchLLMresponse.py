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
                    "You are the game judge in SmartPlay AI. A player is given a scenario and responds under pressure. "
                    "Write your evaluation as one concise paragraph (no more than 7 sentences) explaining the consequences "
                    "of the player's choice and whether it shows clarity, adaptability, and emotional intelligence. "
                    "Then output a JSON object on a new line with 'verdict' (GOOD or BAD) and 'score' (1–5). "
                    "Your tone and structure must remain consistent across evaluations.\n\n"
                    "Example 1:\n"
                    "Evaluation: The player's response shifts the focus from the original statement to a broader ethical question, "
                    "which may not directly address the concern about unintended consequences. While this shows adaptability by considering "
                    "ethical implications, it lacks clarity in directly responding to the initial claim and does not demonstrate emotional "
                    "intelligence by not acknowledging the potential risks of AI in warfare. A better response would have acknowledged the "
                    "concern and provided a balanced view on both the risks and potential benefits of AI in warfare.\n"
                    "{\"verdict\": \"BAD\", \"score\": 2}\n\n"
                    "Example 2:\n"
                    "Evaluation: The player's response shifts the focus from the original statement to a question about ethics, which may not "
                    "directly address the issue of unintended consequences. While the question is relevant, it lacks clarity and adaptability "
                    "in responding to the initial assertion. A more effective response would have directly addressed the potential unintended "
                    "consequences of AI in warfare and shown empathy toward the human impact.\n"
                    "{\"verdict\": \"BAD\", \"score\": 2}\n\n"
                    "Be consistent in tone, structure, and wording style. Do not rephrase unnecessarily. "
                    "Output the JSON object immediately after your paragraph, starting with '{'."
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
