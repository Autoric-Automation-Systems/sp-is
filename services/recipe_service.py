"""Persistência de receitas (JSON + imagem de referência)."""
import json
import logging
import os
import re
import tempfile
from datetime import datetime

import cv2

from paths import IMAGES_DIR, RECIPES_DIR, resolve_project_path, to_project_relative

LOGGER = logging.getLogger(__name__)

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def ensure_dirs():
    RECIPES_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def _slug(name):
    """Gera um nome de arquivo seguro a partir do nome da receita."""
    return _SLUG_RE.sub("_", (name or "").strip().lower()).strip("_")


def normalize_roi(roi, frame_shape=None):
    """Ordena as coordenadas e, se `frame_shape` for informado, limita ao frame.

    Retorna None quando o ROI é inválido ou tem área zero.
    """
    try:
        x1, y1 = int(roi["x1"]), int(roi["y1"])
        x2, y2 = int(roi["x2"]), int(roi["y2"])
    except (KeyError, TypeError, ValueError):
        return None

    x1, x2 = sorted((x1, x2))
    y1, y2 = sorted((y1, y2))

    if frame_shape is not None:
        height, width = frame_shape[:2]
        x1, x2 = max(0, min(x1, width)), max(0, min(x2, width))
        y1, y2 = max(0, min(y1, height)), max(0, min(y2, height))

    if x1 == x2 or y1 == y2:
        return None

    return {"x1": x1, "y1": y1, "x2": x2, "y2": y2}


def _write_json(path, data):
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.stem}-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            f.write("\n")
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def save_recipe(name, roi, frame, original_name=None):
    """Salva receita e imagem de referência. `frame` deve estar em BGR."""
    name = (name or "").strip()
    if not name:
        return False, "Nome obrigatório"

    slug = _slug(name)
    if not slug:
        return False, "Nome inválido"

    if frame is None:
        return False, "Nenhum quadro capturado da câmera"

    normalized_roi = normalize_roi(roi, frame.shape)
    if normalized_roi is None:
        return False, "Selecione um ROI válido (área diferente de zero)"

    ensure_dirs()

    original_slug = _slug(original_name) if original_name else None
    json_path = RECIPES_DIR / f"{slug}.json"
    image_path = IMAGES_DIR / f"{slug}.jpg"

    if json_path.exists() and slug != original_slug:
        return False, "Já existe uma receita com esse nome"

    bgr_frame = frame
    if bgr_frame.ndim == 3 and bgr_frame.shape[2] == 4:
        bgr_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGRA2BGR)

    try:
        ok, encoded = cv2.imencode(".jpg", bgr_frame)
    except cv2.error as exc:
        LOGGER.exception("Falha ao codificar a imagem da receita %s", name)
        return False, f"Falha ao codificar a imagem: {exc}"
    if not ok:
        return False, "Falha ao codificar a imagem"

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if original_slug:
        old_json = RECIPES_DIR / f"{original_slug}.json"
        try:
            with old_json.open(encoding="utf-8") as f:
                created_at = json.load(f).get("created_at", created_at)
        except (OSError, ValueError):
            pass

    data = {
        "name": name,
        "image": to_project_relative(image_path),
        "roi": normalized_roi,
        "created_at": created_at,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    try:
        fd, tmp_image = tempfile.mkstemp(dir=IMAGES_DIR, prefix=f".{slug}-", suffix=".jpg")
        with os.fdopen(fd, "wb") as f:
            f.write(encoded.tobytes())
        os.replace(tmp_image, image_path)
        _write_json(json_path, data)
    except OSError as exc:
        LOGGER.exception("Falha ao salvar a receita %s", name)
        return False, f"Falha ao salvar: {exc}"

    if original_slug and original_slug != slug:
        for old_path in (RECIPES_DIR / f"{original_slug}.json", IMAGES_DIR / f"{original_slug}.jpg"):
            try:
                old_path.unlink(missing_ok=True)
            except OSError as exc:
                LOGGER.warning("Não foi possível remover %s: %s", old_path, exc)

    return True, None


def list_recipes():
    """Lista receitas válidas, ordenadas por nome. Arquivos corrompidos são ignorados."""
    ensure_dirs()
    recipes = []

    for path in sorted(RECIPES_DIR.glob("*.json")):
        try:
            with path.open(encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict) or not data.get("name"):
                raise ValueError("estrutura inválida")
            roi = normalize_roi(data.get("roi"))
            if roi is None:
                raise ValueError("ROI inválido")
            data["roi"] = roi
            if not data.get("image"):
                data["image"] = to_project_relative(IMAGES_DIR / f"{path.stem}.jpg")
            recipes.append(data)
        except (OSError, ValueError) as exc:
            LOGGER.warning("Receita ignorada (%s): %s", path.name, exc)

    return sorted(recipes, key=lambda recipe: recipe["name"].lower())


def delete_recipe(recipe):
    slug = _slug(recipe.get("name", ""))
    if not slug:
        return False

    try:
        (RECIPES_DIR / f"{slug}.json").unlink(missing_ok=True)
        image = recipe.get("image")
        if image:
            resolve_project_path(image).unlink(missing_ok=True)
    except OSError:
        LOGGER.exception("Falha ao excluir a receita %s", recipe.get("name"))
        return False
    return True
