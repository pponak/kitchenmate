import json
from pathlib import Path

DATA_FILE = Path(__file__).parent / "recipes.json"

def save_recipes(recipes):
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(recipes, file, ensure_ascii=False, indent=2)

def load_recipes():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
        
    except FileNotFoundError:
        return []
    
    except json.JSONDecodeError:
        return []