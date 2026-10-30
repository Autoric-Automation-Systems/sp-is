"""Executa um ciclo de inspeção sobre o frame mais recente da câmera."""
import logging
import time
from datetime import datetime

from components.camera_view import orient_frame
from services.config_service import load_config
from services.io_service import get_io
from services.recipe_service import load_reference_image
from services.vision_service import evaluate_rois
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

    def _result(self, result, ok, config, elapsed_ms=0, frame=None, evaluation=None,
                record=True):
        evaluation = evaluation or {}
        return {
            "timestamp": datetime.now(),
            "recipe": (self.view.app.current_recipe or {}).get("name", "-"),
            "result": result,
            "ok": ok,
            "match": float(evaluation.get("score") or 0.0),
            "elapsed_ms": elapsed_ms,
            "details": evaluation.get("rois") or [],
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

        reference = load_reference_image(recipe)
        evaluation = evaluate_rois(frame, reference, recipe.get("rois"))
        elapsed = max(1, int(round((time.perf_counter() - start) * 1000)))

        status = evaluation["result"]
        ok = bool(evaluation["ok"])

        # Reprovado por um ROI específico: aciona o expulsor.
        if not ok and evaluation.get("failed"):
            self.io.pulse_output("ejector", config["ejector"]["time_ms"])

        self.view.set_status(status, SUCCESS if ok else DANGER, evaluation["rois"])
        self.view.time_label.configure(text=f"{elapsed} ms")

        # Receita sem imagem de referência é erro de configuração, não uma
        # reprovação da peça: não entra nas estatísticas (como "SEM RECEITA").
        return self._result(
            status,
            ok,
            config,
            elapsed,
            frame,
            evaluation,
            record=status != "SEM REFERÊNCIA",
        )
