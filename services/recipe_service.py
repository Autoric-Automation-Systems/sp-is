import os
import json
from datetime import datetime
import cv2

BASE_PATH = "data/recipes"
IMAGE_PATH = "data/images"


def ensure_dirs():
    os.makedirs(BASE_PATH, exist_ok=True)
    os.makedirs(IMAGE_PATH, exist_ok=True)


def save_recipe(name, roi, frame, original_name=None):    
    ensure_dirs()

    filename = name.replace(" ", "_").lower()

    json_file = f"{filename}.json"
    image_file = f"{filename}.jpg"

    json_path = os.path.join(BASE_PATH, json_file)
    image_path = os.path.join(IMAGE_PATH, image_file)

    if os.path.exists(json_path):
        if not original_name or original_name != name:
            return False, "Já existe uma receita com esse nome"

    if original_name and original_name != name:
        old_filename = original_name.replace(" ", "_").lower()

        old_json = os.path.join(BASE_PATH, f"{old_filename}.json")
        old_image = os.path.join(IMAGE_PATH, f"{old_filename}.jpg")

        if os.path.exists(old_json):
            os.remove(old_json)

        if os.path.exists(old_image):
            os.remove(old_image)

    # salva imagem
    cv2.imwrite(image_path, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))


    # Corrige ROI se necessário
    x1, y1, x2, y2 = roi["x1"], roi["y1"], roi["x2"], roi["y2"]
    x1, x2 = min(x1, x2), max(x1, x2)
    y1, y2 = min(y1, y2), max(y1, y2)
    roi = {"x1": x1, "y1": y1, "x2": x2, "y2": y2}

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    data = {
        "name": name,
        "image": image_path,  # salva caminho completo relativo
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
    # Usa o caminho salvo no campo 'image' (já relativo à raiz do projeto)
    image_path = recipe["image"]

    if os.path.exists(json_path):
        os.remove(json_path)

    if os.path.exists(image_path):
        os.remove(image_path)