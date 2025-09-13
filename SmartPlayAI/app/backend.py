from typing import Union
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="SmartPlayAI", version="1.0.0")
# to run this file use: uvicorn backend:app --reload


class Item(BaseModel):
    name: str
    description: Union[str, None] = None
    price: float
    tax: Union[float, None] = None


@app.get("/")
async def root():
    return {"message": "Hello, World, this request was call from backend.py"}


@app.post("/items/")
async def create_item(item: Item):
    return {
        "item_name": item.name, "item_price": item.price, "item_description": item.description, "item_tax": item.tax}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080, log_level="info")
