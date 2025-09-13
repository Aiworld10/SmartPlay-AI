import requests


# Base URL for the API
BASE_URL = "http://127.0.0.1:8080"


# Example function to fetch data from an API
def get_root_message():
    res = requests.get(f"{BASE_URL}/")
    if res.status_code == 200:
        return res.json().get("message")
    return {"error": "Failed to retrieve message"}

# create item from a form


def create_item(name: str, price: float, description: str = None, tax: float = None):
    item_data = {
        "name": name,
        "price": price,
        "description": description,
        "tax": tax
    }
    res = requests.post(f"{BASE_URL}/items/", json=item_data)
    if res.status_code == 200:
        return res.json()
    return {"error": "Failed to create item"}


if __name__ == "__main__":
    print(get_root_message())
    print(create_item(name="Sample Item", price=10.5,
          description="A sample item", tax=0.5))
# To run this file, ensure the backend server is running and execute: python frontend.py
