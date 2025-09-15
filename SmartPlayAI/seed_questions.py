import asyncio
import json
from sqlalchemy.ext.asyncio import AsyncSession
from model.database import AsyncSessionLocal  # Fixed import name
from model import schemas
from model.crud import load_questions_from_json


async def insert_from_json_file(file_path: str):
    async with AsyncSessionLocal() as db:  # Use the correct session maker
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Validate that data is a list
            if not isinstance(data, list):
                raise ValueError(
                    "JSON file should contain a list of questions")

            questions = [schemas.QuestionCreate(**item) for item in data]

            inserted = await load_questions_from_json(db, questions)
            print(f"Inserted {len(inserted)} questions into DB")

        except FileNotFoundError:
            print(f"Error: File '{file_path}' not found")
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in file '{file_path}'")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(insert_from_json_file("static/questions.json"))
