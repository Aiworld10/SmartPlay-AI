#!/usr/bin/env python3
"""
Script to delete all questions from the database.
Use with caution - this will permanently delete all question data!
"""

import asyncio
from model.database import AsyncSessionLocal
from model.crud import delete_all_questions


async def clear_all_questions():
    """Delete all questions from the database."""
    async with AsyncSessionLocal() as db:
        try:
            deleted_count = await delete_all_questions(db)
            print(
                f"Successfully deleted {deleted_count} questions from the database.")

        except Exception as e:
            print(f"Error deleting questions: {e}")


if __name__ == "__main__":
    # Ask for confirmation before deleting
    response = input(
        "This will delete ALL questions from the database. Are you sure? (yes/no): ")

    if response.lower() in ['yes', 'y']:
        asyncio.run(clear_all_questions())
        print("Database cleared.")
    else:
        print("Operation cancelled.")
