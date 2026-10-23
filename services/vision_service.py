"""Comparação de ROI baseada em densidade de bordas (Canny).

Contrato: os frames entram em BGR (3 canais) ou BGRA.
"""
import cv2
import numpy as np


def clamp_roi(roi_coords, frame_shape):
    """Retorna o ROI ordenado e limitado ao frame, ou None se inválido."""
    if not roi_coords:
        return None

    height, width = frame_shape[:2]
    try:
        x1, y1 = int(roi_coords["x1"]), int(roi_coords["y1"])
        x2, y2 = int(roi_coords["x2"]), int(roi_coords["y2"])
    except (KeyError, TypeError, ValueError):
        return None

    x1, x2 = sorted((max(0, min(x1, width)), max(0, min(x2, width))))
    y1, y2 = sorted((max(0, min(y1, height)), max(0, min(y2, height))))

    if x1 == x2 or y1 == y2:
        return None

    return {"x1": x1, "y1": y1, "x2": x2, "y2": y2}


def crop_roi(frame, roi_coords):
    """Recorta o ROI limitando as coordenadas ao tamanho do frame."""
    if frame is None:
        return None
    coords = clamp_roi(roi_coords, frame.shape)
    if coords is None:
        return None
    return frame[coords["y1"]:coords["y2"], coords["x1"]:coords["x2"]]


def _to_gray(image):
    if image.ndim == 3 and image.shape[2] == 4:
        return cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
    if image.ndim == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return image


def compare_roi(frame, roi_coords, threshold_edges):
    """Detecta a presença da tampa pela densidade de bordas e brilho médio.

    A tampa lisa e clara gera poucas bordas; o bocal aberto (roscas) gera muitas.
    """
    roi = crop_roi(frame, roi_coords)
    if roi is None:
        return {
            "valid": False,
            "missing_cap": None,
            "edge_score": 0,
            "brightness": 0.0,
            "debug_view": None,
            "error": "ROI inválido",
        }

    try:
        threshold_edges = float(threshold_edges)
    except (TypeError, ValueError):
        threshold_edges = 0.0

    gray = _to_gray(roi)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 50, 150)

    edge_density = int(cv2.countNonZero(edges))
    avg_brightness = float(np.mean(gray))

    return {
        "valid": True,
        "missing_cap": edge_density > threshold_edges,
        "edge_score": edge_density,
        "brightness": avg_brightness,
        "debug_view": edges,
    }
