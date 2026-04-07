import cv2
import numpy as np

def compare_roi(frame, roi_coords, threshold_edges):
    """
    Detecta a presença da tampa baseando-se na densidade de bordas e brilho médio.
    """
    x, y, w, h = roi_coords['x1'], roi_coords['y1'], roi_coords['x2']-roi_coords['x1'], roi_coords['y2']-roi_coords['y1']
    roi = frame[y:y+h, x:x+w]

    # 1. Pré-processamento
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # 2. Detecção de Bordas (Canny)
    # Ajuste os valores 50, 150 conforme a iluminação do seu ambiente
    edges = cv2.Canny(blur, 50, 150)
    
    # Conta quantos pixels de borda foram encontrados
    edge_density = np.sum(edges > 0)

    # 3. Análise de Brilho Médio (Opcional, mas ajuda muito)
    avg_brightness = np.mean(gray)

    # Lógica de Decisão:
    # A tampa branca é lisa (poucas bordas internas) e clara (alto brilho).
    # O bocal aberto tem roscas (muitas bordas) e é mais escuro/sombreado.
    
    is_missing = edge_density > threshold_edges
    
    return {
        "missing_cap": bool(is_missing),
        "edge_score": edge_density,
        "brightness": avg_brightness,
        "debug_view": edges # Retorne isso para ajustar o threshold visualmente
    }