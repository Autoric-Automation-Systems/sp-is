import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim


def compare_roi(frame, reference_img, roi):
    x1, y1, x2, y2 = roi.values()

    # recorte atual
    current = frame[y1:y2, x1:x2]
    # Se vier com 4 canais (RGBA), converte para 3 canais (RGB)
    if current.ndim == 3 and current.shape[2] == 4:
        current = cv2.cvtColor(current, cv2.COLOR_BGRA2BGR)

    # 🔥 GARANTE QUE reference_img É IMAGEM
    if isinstance(reference_img, str):
        reference_img = cv2.imread(reference_img)

    if reference_img is None:
        raise ValueError("Imagem de referência inválida ou não encontrada. Verifique se a receita foi salva corretamente e se a imagem existe.")

    # Protege contra ROI inválido
    if current.shape[0] == 0 or current.shape[1] == 0:
        raise ValueError("ROI inválido: área selecionada é zero.")

    # redimensiona
    try:
        ref = cv2.resize(reference_img, (current.shape[1], current.shape[0]))
    except cv2.error as e:
        raise ValueError(f"Erro ao redimensionar imagem de referência: {e}")

    # SSIM
    if current.shape != ref.shape:
        raise ValueError(f"As imagens comparadas têm tamanhos diferentes: atual={current.shape}, referência={ref.shape}. Verifique o ROI e salve a receita novamente.")
    # Converte para escala de cinza para SSIM
    gray_current = cv2.cvtColor(current, cv2.COLOR_BGR2GRAY)
    gray_ref = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY)
    ssim_score, _ = ssim(gray_current, gray_ref, full=True)
    # Para manter compatibilidade com threshold, retorna 1-ssim (quanto menor, mais parecido)
    return 1 - ssim_score