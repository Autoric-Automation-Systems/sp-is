import os
import json
from datetime import datetime
import cv2

BASE_PATH = "data/recipes"
IMAGE_PATH = "data/images"


def ensure_dirs():
    os.makedirs(BASE_PATH, exist_ok=True)
    os.makedirs(IMAGE_PATH, exist_ok=True)


def save_recipe(name, roi, frame):
    ensure_dirs()

    filename = name.replace(" ", "_").lower()

    json_file = f"{filename}.json"
    image_file = f"{filename}.jpg"

    json_path = os.path.join(BASE_PATH, json_file)
    image_path = os.path.join(IMAGE_PATH, image_file)

    # 🚫 valida duplicado
    if os.path.exists(json_path):
        return False, "Já existe uma receita com esse nome"

    # salva imagem
    cv2.imwrite(image_path, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    data = {
        "name": name,
        "image": image_file,
        "roi": roi,
        "created_at": now,
        "updated_at": now
    }

    with open(json_path, "w") as f:
        json.dump(data, f, indent=2)

    return True, None


def list_recipes():
    ensure_dirs()

    files = [f for f in os.listdir(BASE_PATH) if f.endswith(".json")]

    recipes = []

    for file in files:
        with open(os.path.join(BASE_PATH, file)) as f:
            recipes.append(json.load(f))

    return recipes


def delete_recipe(recipe):
    filename = recipe["name"].replace(" ", "_").lower()

    json_path = os.path.join(BASE_PATH, f"{filename}.json")
    image_path = os.path.join(IMAGE_PATH, recipe["image"])

    if os.path.exists(json_path):
        os.remove(json_path)

    if os.path.exists(image_path):
        os.remove(image_path)