"""Executa um ciclo de inspeção sobre o frame mais recente da câmera."""
import logging
import time
from datetime import datetime

from components.camera_view import orient_frame
from services.config_service import load_config
from services.io_service import get_io
from services.vision_service import compare_roi
from styles.theme import DANGER, SUCCESS

LOGGER = logging.getLogger(__name__)

TRIGGER_LED_PULSE_MS = 120


class RunCycle:
    def __init__(self, view):
        self.view = view
        self.io = get_io()

    def __call__(self):
        """Permite usar a instância como callback de botão do Tkinter."""
        return self.run()

    def _result(self, result, ok, config, elapsed_ms=0, frame=None, score=0,
                brightness=0.0, record=True):
        return {
            "timestamp": datetime.now(),
            "recipe": (self.view.app.current_recipe or {}).get("name", "-"),
            "result": result,
            "ok": ok,
            "score": score,
            "threshold": config.get("threshold", 0),
            "brightness": brightness,
            "elapsed_ms": elapsed_ms,
            "frame": frame,
            "record": record,
        }

    def run(self):
        config = load_config()
        recipe = self.view.app.current_recipe

        if not recipe:
            self.view.set_status("SEM RECEITA", DANGER)
            return self._result("SEM RECEITA", False, config, record=False)

        self.io.pulse_output("led", TRIGGER_LED_PULSE_MS)

        start = time.perf_counter()

        try:
            frame = self.view.camera.get_frame()
        except Exception:
            LOGGER.exception("Falha ao capturar frame")
            frame = None

        if frame is None:
            self.view.set_status("CÂMERA INDISPONÍVEL", DANGER)
            return self._result("CÂMERA INDISPONÍVEL", False, config)

        frame = orient_frame(frame, config.get("rotate_180", True))
        result = compare_roi(frame, recipe.get("roi"), config["threshold"])
        elapsed = max(1, int(round((time.perf_counter() - start) * 1000)))

        if not result["valid"]:
            self.view.set_status("ROI INVÁLIDO", DANGER)
            self.view.time_label.configure(text=f"{elapsed} ms")
            return self._result("ROI INVÁLIDO", False, config, elapsed, frame)

        score = result["edge_score"]
        brightness = result["brightness"]
        threshold = config["threshold"]

        if brightness < config["min_brightness"]:
            status, ok = "SEM GARRAFA", False
        elif score > threshold:
            status, ok = "ERRO: SEM TAMPA", False
        else:
            status, ok = "OK", True

        if not ok and status == "ERRO: SEM TAMPA":
            self.io.pulse_output("ejector", config["ejector"]["time_ms"])

        self.view.set_status(status, SUCCESS if ok else DANGER, score, threshold)
        self.view.time_label.configure(text=f"{elapsed} ms")

        return self._result(
            status,
            ok,
            config,
            elapsed_ms=elapsed,
            frame=frame,
            score=score,
            brightness=brightness,
        )
