"""Persistência de receitas (JSON + imagem de referência).

Uma receita tem exatamente `ROI_COUNT` regiões de inspeção, cada uma com nome
editável, retângulo em coordenadas da imagem e uma janela de acerto em %
(comparada à imagem de referência guardada junto da receita).

Receitas antigas, com um único `roi`, são convertidas automaticamente: o ROI
existente vira o primeiro e o segundo é criado logo abaixo dele.
"""
import json
import logging
import os
import re
import tempfile
from datetime import datetime

import cv2
import numpy as np

from paths import IMAGES_DIR, RECIPES_DIR, resolve_project_path, to_project_relative
from services.vision_service import (
    DEFAULT_MAX_MATCH,
    DEFAULT_MIN_MATCH,
    normalize_window,
)

LOGGER = logging.getLogger(__name__)

_SLUG_RE = re.compile(r"[^a-z0-9]+")

ROI_COUNT = 3
MAX_ROI_NAME_LENGTH = 24
DEFAULT_ROI_NAMES = ("Tampa", "Nível")
# Cores dos ROIs na interface: sem verde e sem vermelho, que ficam reservados
# para o resultado (aprovado/reprovado).
ROI_COLORS = ("#38bdf8", "#fbbf24", "#a78bfa", "#22d3ee")

# Regiões iniciais de uma receita nova (proporção da imagem): tampa no alto,
# nível abaixo e uma terceira região livre. O operador ajusta com mouse ou X/Y.
_DEFAULT_ROI_BANDS = (
    (0.40, 0.10, 0.60, 0.25),
    (0.40, 0.45, 0.60, 0.60),
    (0.40, 0.78, 0.60, 0.93),
)

_reference_cache = {}


def roi_color(index):
    """Cor do ROI na interface (mesma ordem usada nos overlays e nos cards)."""
    return ROI_COLORS[index % len(ROI_COLORS)]


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


def default_roi_name(index):
    """Nome padrão do ROI (Tampa, Nível, ROI 3...)."""
    if index < len(DEFAULT_ROI_NAMES):
        return DEFAULT_ROI_NAMES[index]
    return f"ROI {index + 1}"


def normalize_roi_name(name, index):
    """Nome do ROI sem espaços sobrando, truncado ao limite."""
    text = str(name or "").strip()
    return text[:MAX_ROI_NAME_LENGTH] or default_roi_name(index)


def _default_band(index, frame_shape):
    height, width = frame_shape[:2]
    left, top, right, bottom = _DEFAULT_ROI_BANDS[min(index, len(_DEFAULT_ROI_BANDS) - 1)]
    return {
        "x1": int(round(width * left)),
        "y1": int(round(height * top)),
        "x2": int(round(width * right)),
        "y2": int(round(height * bottom)),
    }


def default_roi_entry(index, frame_shape=(480, 640)):
    """ROI inicial de uma receita nova."""
    return {
        "name": default_roi_name(index),
        "roi": _default_band(index, frame_shape),
        "min_match": DEFAULT_MIN_MATCH,
        "max_match": DEFAULT_MAX_MATCH,
    }


def _roi_below(box, frame_shape):
    """Cria um ROI logo abaixo de outro (usado na migração das receitas antigas)."""
    height, width = frame_shape[:2]
    x1, x2 = box["x1"], box["x2"]
    roi_height = max(2, box["y2"] - box["y1"])
    y1 = min(box["y2"] + max(4, roi_height // 4), height - 2)
    y2 = min(height, y1 + roi_height)
    if y2 - y1 < 2:
        y1, y2 = 0, min(height, roi_height)
    return {"x1": x1, "y1": y1, "x2": x2, "y2": y2}


def normalize_roi_entry(entry, index, frame_shape=None):
    """Normaliza um ROI da receita; None quando as coordenadas são inválidas."""
    entry = entry if isinstance(entry, dict) else {}
    box = normalize_roi(entry.get("roi") or entry, frame_shape)
    if box is None:
        return None

    min_match, max_match = normalize_window(
        entry.get("min_match"), entry.get("max_match")
    )
    return {
        "name": normalize_roi_name(entry.get("name"), index),
        "roi": box,
        "min_match": min_match,
        "max_match": max_match,
    }


def _migrate_single_roi(data, frame_shape):
    """Converte {"roi": {...}} (formato antigo) em `ROI_COUNT` ROIs.

    Os ROIs novos (criados abaixo do original) entram com janela 0–100%: não
    reprovam peça nenhuma até o operador calibrá-los no editor, evitando que uma
    região inventada derrube a produção logo após a atualização.
    """
    entries = [{"name": default_roi_name(0), "roi": data["roi"]}]
    box = normalize_roi(data["roi"], frame_shape)
    if box is not None:
        for index in range(1, ROI_COUNT):
            entries.append(
                {
                    "name": default_roi_name(index),
                    "roi": _roi_below(box, frame_shape),
                    "min_match": 0.0,
                    "max_match": 100.0,
                }
            )
    return entries


def _unique_names(entries):
    """Garante nomes distintos para que o resultado identifique o ROI."""
    seen = {}
    for entry in entries:
        base = entry["name"]
        count = seen.get(base.lower(), 0) + 1
        seen[base.lower()] = count
        if count > 1:
            entry["name"] = f"{base} {count}"[:MAX_ROI_NAME_LENGTH]
    return entries


def normalize_rois(rois, frame_shape=(480, 640)):
    """Normaliza a lista de ROIs da receita (sempre `ROI_COUNT` entradas).

    Receitas gravadas com menos ROIs que o modelo atual recebem as regiões
    restantes com janela 0–100% (inertes até serem calibradas).
    """
    if isinstance(rois, dict):
        rois = _migrate_single_roi({"roi": rois}, frame_shape)
    if not isinstance(rois, (list, tuple)) or not rois:
        return []

    normalized = []
    for index, entry in enumerate(list(rois)[:ROI_COUNT]):
        item = normalize_roi_entry(entry, index, frame_shape)
        if item is not None:
            normalized.append(item)

    if not normalized:
        return []

    while len(normalized) < ROI_COUNT:
        entry = default_roi_entry(len(normalized), frame_shape)
        entry["min_match"] = 0.0
        entry["max_match"] = 100.0
        normalized.append(entry)

    return _unique_names(normalized)


def load_reference_image(recipe):
    """Imagem de referência da receita em BGR (ou None se não existir)."""
    image = (recipe or {}).get("image")
    if not image:
        return None

    path = resolve_project_path(image)
    try:
        stamp = path.stat().st_mtime
    except OSError:
        return None

    key = (str(path), stamp)
    cached = _reference_cache.get(key)
    if cached is not None:
        return cached

    try:
        buffer = np.fromfile(str(path), dtype=np.uint8)
        frame = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
    except (OSError, ValueError):
        LOGGER.exception("Falha ao ler a imagem de referência %s", path)
        return None

    if frame is None:
        LOGGER.warning("Imagem de referência ilegível: %s", path)
        return None

    _reference_cache.clear()
    _reference_cache[key] = frame
    return frame


def save_recipe(name, rois, frame, original_name=None):
    """Salva receita e imagem de referência. `rois` traz os `ROI_COUNT` ROIs."""
    name = (name or "").strip()
    if not name:
        return False, "Nome obrigatório"

    slug = _slug(name)
    if not slug:
        return False, "Nome inválido"

    if frame is None:
        return False, "Nenhum quadro capturado da câmera"

    if not isinstance(rois, (list, tuple)) or len(rois) != ROI_COUNT:
        return False, f"A receita precisa de {ROI_COUNT} ROIs"

    normalized = []
    for index, entry in enumerate(rois):
        item = normalize_roi_entry(entry, index, frame.shape)
        if item is None:
            return False, f"ROI {index + 1}: selecione uma área válida (diferente de zero)"
        normalized.append(item)

    names = [item["name"].lower() for item in normalized]
    if len(set(names)) != len(names):
        return False, "Cada ROI deve ter um nome diferente"

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
        "rois": normalized,
        "created_at": created_at,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    tmp_image = None
    tmp_json = None
    try:
        # Prepara os dois arquivos antes de publicar: evita deixar a imagem
        # nova apontando para o JSON antigo e não vaza temporário em caso de erro.
        fd, tmp_image = tempfile.mkstemp(dir=IMAGES_DIR, prefix=f".{slug}-", suffix=".jpg")
        with os.fdopen(fd, "wb") as f:
            f.write(encoded.tobytes())
        fd, tmp_json = tempfile.mkstemp(dir=RECIPES_DIR, prefix=f".{slug}-", suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            f.write("\n")
        os.replace(tmp_image, image_path)
        tmp_image = None
        os.replace(tmp_json, json_path)
        tmp_json = None
    except OSError as exc:
        LOGGER.exception("Falha ao salvar a receita %s", name)
        return False, f"Falha ao salvar: {exc}"
    finally:
        for leftover in (tmp_image, tmp_json):
            if leftover and os.path.exists(leftover):
                try:
                    os.unlink(leftover)
                except OSError:
                    pass

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
            rois = normalize_rois(data.get("rois") or data.get("roi"))
            if len(rois) != ROI_COUNT:
                raise ValueError("ROIs insuficientes ou inválidos")
            data["rois"] = rois
            data.pop("roi", None)
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
