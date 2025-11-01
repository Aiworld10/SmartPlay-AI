import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("="*60)
print("ENVIRONMENT VARIABLE CHECK")
print("="*60)
serveo_host = os.getenv("SERVEO_HOST")
print(f"SERVEO_HOST: {serveo_host}")
print(f"Is None: {serveo_host is None}")
print()

# Test the evaluation function
print("="*60)
print("TESTING EVALUATION FUNCTION")
print("="*60)

from fetchLLMresponse import evaluate_player_response

question = "Work situation: Your written reports are accurate but full of typos and formatting mistakes. How do you handle this?"
answer = "I would review my work carefully and use spell-check tools to ensure quality before submission."

print(f"Question: {question}")
print(f"Answer: {answer}")
print()
print("Calling evaluation function...")
print()

try:
    evaluation_text, result = evaluate_player_response(question, answer)
    print("SUCCESS!")
    print(f"Evaluation Text: {evaluation_text}")
    print(f"Result: {result}")
    print(f"Verdict: {result.get('verdict')}")
    print(f"Score: {result.get('score')}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*60)
