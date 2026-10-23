"""Diálogo com a imagem analisada em tamanho grande."""
import customtkinter as ctk
import cv2
from PIL import Image, ImageOps

from components import ui
from services.vision_service import clamp_roi
from styles.theme import *

PREVIEW_WIDTH = 820
PREVIEW_HEIGHT = 520


def record_image(record, size, overlay_roi=None):
    """Converte o frame gravado em PIL, opcionalmente desenhando o ROI."""
    frame = record.frame_bgr()
    if frame is None:
        return None

    if overlay_roi is not None:
        frame = frame.copy()
        box = clamp_roi(overlay_roi, frame.shape)
        if box is not None:
            color = (16, 185, 129) if record.ok else (244, 63, 94)
            cv2.rectangle(
                frame,
                (box["x1"], box["y1"]),
                (box["x2"], box["y2"]),
                color,
                2,
            )

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return ImageOps.contain(Image.fromarray(rgb), size, Image.LANCZOS)


class AnalysisDialog:
    """Mostra a captura analisada com o resultado e as métricas do ciclo."""

    def __init__(self, parent, record, roi=None):
        self.window = ctk.CTkToplevel(parent)
        self.window.title(f"Captura analisada · {record.time_text}")
        self.window.configure(fg_color=BG)
        self.window.transient(parent)
        self.window.resizable(False, False)

        card = ctk.CTkFrame(
            self.window,
            fg_color=CARD,
            corner_radius=10,
            border_width=1,
            border_color=BORDER,
        )
        card.pack(fill="both", expand=True, padx=10, pady=10)

        header = ctk.CTkFrame(card, fg_color=CARD, corner_radius=0)
        header.pack(fill="x", padx=16, pady=(14, 6))
        ui.label(
            header,
            record.result,
            kind="header",
            bg=CARD,
            fg=SUCCESS if record.ok else DANGER,
        ).pack(side="left")
        ui.label(
            header,
            f"{record.time_text} · {record.recipe}",
            kind="small",
            bg=CARD,
        ).pack(side="left", padx=(12, 0))

        image = record_image(record, (PREVIEW_WIDTH, PREVIEW_HEIGHT), overlay_roi=roi)
        if image is not None:
            self._photo = ctk.CTkImage(light_image=image, dark_image=image, size=image.size)
            ctk.CTkLabel(card, image=self._photo, text="", fg_color=CARD).pack(
                padx=16, pady=6
            )
        else:
            ui.label(card, "Imagem não disponível para esta captura.", kind="muted", bg=CARD).pack(
                padx=16, pady=40
            )

        metrics = ctk.CTkFrame(card, fg_color=CARD, corner_radius=0)
        metrics.pack(fill="x", padx=16, pady=(4, 8))
        for index, (key, value) in enumerate(
            (
                ("Score", str(record.score)),
                ("Limiar", f"{record.threshold:g}"),
                ("Brilho", f"{record.brightness:.0f}"),
                ("Tempo", f"{record.elapsed_ms} ms"),
            )
        ):
            ui.label(metrics, key, kind="small", bg=CARD).grid(
                row=0, column=index * 2, sticky="w", padx=(0, 6)
            )
            ui.label(metrics, value, kind="bold", bg=CARD).grid(
                row=0, column=index * 2 + 1, sticky="w", padx=(0, 22)
            )

        ui.button(
            card,
            "Fechar",
            command=self.window.destroy,
            variant="secondary",
            size="md",
        ).pack(fill="x", padx=16, pady=(0, 14))

        self.window.bind("<Escape>", lambda _event: self.window.destroy())
        self.window.update_idletasks()
        width = max(self.window.winfo_reqwidth(), 520)
        height = self.window.winfo_reqheight()
        x = parent.winfo_rootx() + max(0, (parent.winfo_width() - width) // 2)
        y = parent.winfo_rooty() + max(0, (parent.winfo_height() - height) // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        self.window.grab_set()
