import time
import cv2
from services.config_service import load_config
from services.vision_service import compare_roi
from styles.theme import *

class RunCycle:
    def __init__(self, view):
        self.view = view

    def __call__(self):
        """Faz a classe ser chamável como uma função pelo botão do Tkinter"""
        config = load_config()
        threshold_edges = config.get("threshold", 500) 
        min_brightness = config.get("min_brightness", 150) 

        if not self.view.app.current_recipe:
            self.view.set_status("SEM RECEITA", DANGER)
            return

        start = time.time()
        
        # 1. Captura e Rotaciona usando a câmera da View
        frame = self.view.camera.get_frame()
        frame = cv2.rotate(frame, cv2.ROTATE_180)
        
        roi_coords = self.view.app.current_recipe["roi"]
        
        # 2. Processamento
        result = compare_roi(frame, roi_coords, threshold_edges)
        
        score = result["edge_score"]
        brightness = result["brightness"]
        
        elapsed = int((time.time() - start) * 1000)

        # 3. Lógica de Decisão atualizada
        if brightness < min_brightness:
            self.view.set_status("SEM GARRAFA", DANGER, score, threshold_edges)
        elif score > threshold_edges:
            self.view.set_status("ERRO: SEM TAMPA", DANGER, score, threshold_edges)
        else:
            self.view.set_status("OK", SUCCESS, score, threshold_edges)
            
        self.view.time_label.config(text=f"{elapsed} ms")