"""Avaliação das ROIs de inspeção por similaridade com a referência.

Cada ROI da receita tem uma janela de acerto em %:

- a métrica é o SSIM (índice de similaridade estrutural) entre o ROI do frame
  ao vivo e o mesmo ROI recortado da imagem de referência da receita;
- 100% significa região idêntica à referência; valores menores indicam desvio
  (tampa ausente, nível diferente, peça torta, sujeira, iluminação fora do
  padrão...);
- o ROI é aprovado quando o percentual fica dentro de [min_match, max_match].

Contrato: os frames entram em BGR (3 canais) ou BGRA.
"""
import cv2
import numpy as np

DEFAULT_MIN_MATCH = 85.0
DEFAULT_MAX_MATCH = 100.0

_SSIM_KERNEL = 11
_SSIM_SIGMA = 1.5
_SSIM_C1 = (0.01 * 255) ** 2
_SSIM_C2 = (0.03 * 255) ** 2


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


def _ssim_kernel(height, width):
    """Kernel ímpar que cabe na imagem (SSIM exige vizinhança)."""
    size = min(_SSIM_KERNEL, height, width)
    if size % 2 == 0:
        size -= 1
    return max(3, size)


def ssim_percent(reference_gray, frame_gray):
    """Similaridade estrutural entre duas imagens de mesmo tamanho, em 0–100%."""
    if reference_gray is None or frame_gray is None:
        return 0.0

    if reference_gray.shape[:2] != frame_gray.shape[:2]:
        frame_gray = cv2.resize(
            frame_gray,
            (reference_gray.shape[1], reference_gray.shape[0]),
            interpolation=cv2.INTER_AREA,
        )

    height, width = reference_gray.shape[:2]
    if height < 2 or width < 2:
        return 0.0

    kernel = _ssim_kernel(height, width)
    size = (kernel, kernel)
    a = reference_gray.astype(np.float64)
    b = frame_gray.astype(np.float64)

    mean_a = cv2.GaussianBlur(a, size, _SSIM_SIGMA)
    mean_b = cv2.GaussianBlur(b, size, _SSIM_SIGMA)
    mean_aa = mean_a * mean_a
    mean_bb = mean_b * mean_b
    mean_ab = mean_a * mean_b

    var_a = cv2.GaussianBlur(a * a, size, _SSIM_SIGMA) - mean_aa
    var_b = cv2.GaussianBlur(b * b, size, _SSIM_SIGMA) - mean_bb
    cov_ab = cv2.GaussianBlur(a * b, size, _SSIM_SIGMA) - mean_ab

    numerator = (2 * mean_ab + _SSIM_C1) * (2 * cov_ab + _SSIM_C2)
    denominator = (mean_aa + mean_bb + _SSIM_C1) * (var_a + var_b + _SSIM_C2)
    ratio = np.divide(
        numerator,
        denominator,
        out=np.ones_like(numerator),
        where=denominator != 0,
    )

    similarity = float(np.clip(ratio.mean(), -1.0, 1.0))
    return round(max(0.0, similarity) * 100.0, 1)


def match_percent(frame, reference, roi_coords):
    """% de acerto do ROI do frame comparado ao mesmo ROI da referência."""
    frame_roi = crop_roi(frame, roi_coords)
    reference_roi = crop_roi(reference, roi_coords)
    if frame_roi is None or reference_roi is None:
        return None
    return ssim_percent(_to_gray(reference_roi), _to_gray(frame_roi))


def parse_percent(value):
    """Converte texto/float em % (aceita vírgula decimal); None se inválido."""
    if value is None:
        return None
    try:
        number = float(str(value).strip().replace(",", "."))
    except (TypeError, ValueError):
        return None
    if number != number:  # NaN
        return None
    return min(100.0, max(0.0, number))


def _as_percent(value, default):
    parsed = parse_percent(value)
    return float(default) if parsed is None else parsed


def normalize_window(min_match=None, max_match=None):
    """Janela de acerto ordenada e limitada a 0–100%."""
    low = _as_percent(min_match, DEFAULT_MIN_MATCH)
    high = _as_percent(max_match, DEFAULT_MAX_MATCH)
    if low > high:
        low, high = high, low
    return low, high


def _roi_box(roi_spec, frame_shape):
    """Aceita {"roi": {...}} ou o próprio retângulo, já limitado ao frame."""
    if isinstance(roi_spec, dict) and isinstance(roi_spec.get("roi"), dict):
        roi_spec = roi_spec["roi"]
    return clamp_roi(roi_spec, frame_shape)


def evaluate_rois(frame, reference, rois):
    """Avalia todos os ROIs da receita e devolve o resultado por ROI e agregado.

    `rois` é a lista salva na receita: {"name", "roi", "min_match", "max_match"}.
    Quando mais de um ROI reprova, todos aparecem no resultado agregado
    (`ERRO: TAMPA, NÍVEL`) e em `failed`.
    """
    empty = {"valid": False, "ok": False, "failed": [], "score": 0.0, "rois": []}

    if frame is None:
        return {**empty, "result": "CÂMERA INDISPONÍVEL", "error": "sem frame"}

    specs = list(rois or [])
    if not specs:
        return {**empty, "result": "ROI INVÁLIDO", "error": "receita sem ROIs"}

    resized_reference = reference
    if reference is not None and reference.shape[:2] != frame.shape[:2]:
        resized_reference = cv2.resize(
            reference,
            (frame.shape[1], frame.shape[0]),
            interpolation=cv2.INTER_AREA,
        )

    results = []
    for index, spec in enumerate(specs):
        spec = spec if isinstance(spec, dict) else {}
        name = str(spec.get("name") or "").strip() or f"ROI {index + 1}"
        min_match, max_match = normalize_window(
            spec.get("min_match"), spec.get("max_match")
        )
        box = _roi_box(spec, frame.shape)

        entry = {
            "name": name,
            "min": min_match,
            "max": max_match,
            "match": None,
            "ok": False,
            "x1": None,
            "y1": None,
            "x2": None,
            "y2": None,
        }

        if box is None:
            entry["error"] = "ROI inválido"
        elif resized_reference is None:
            entry["error"] = "referência ausente"
        else:
            entry.update(box)
            match = match_percent(frame, resized_reference, box)
            if match is None:
                entry["error"] = "ROI inválido"
            else:
                entry["match"] = match
                entry["ok"] = min_match <= match <= max_match

        results.append(entry)

    if resized_reference is None:
        return {**empty, "result": "SEM REFERÊNCIA", "rois": results}
    if any("ROI inválido" in str(entry.get("error", "")) for entry in results):
        return {**empty, "result": "ROI INVÁLIDO", "rois": results}

    failed = [entry["name"] for entry in results if not entry["ok"]]
    matches = [entry["match"] for entry in results if entry["match"] is not None]
    return {
        "valid": True,
        "ok": not failed,
        "result": "OK" if not failed else "ERRO: " + " + ".join(name.upper() for name in failed),
        "failed": failed,
        "score": min(matches) if matches else 0.0,
        "rois": results,
    }
