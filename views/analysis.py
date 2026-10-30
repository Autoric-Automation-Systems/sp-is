"""Diálogo com a imagem analisada em tamanho grande."""
import customtkinter as ctk
import cv2
from PIL import Image, ImageOps

from components import ui
from services.recipe_service import ROI_COLORS
from services.vision_service import clamp_roi
from styles.theme import *

PREVIEW_WIDTH = 820
PREVIEW_HEIGHT = 520


def record_image(record, size, overlay=False):
    """Converte o frame gravado em PIL, opcionalmente desenhando os ROIs.

    Os retângulos e as cores vêm dos `details` guardados na própria inspeção,
    então a imagem continua correta mesmo após a receita ser editada.
    """
    frame = record.frame_bgr()
    if frame is None:
        return None

    details = [entry for entry in (record.details or []) if isinstance(entry, dict)]
    if overlay and details:
        frame = frame.copy()
        for index, entry in enumerate(details):
            box = clamp_roi(entry, frame.shape)
            if box is None:
                continue
            color = _BGR_COLORS[index % len(_BGR_COLORS)]
            cv2.rectangle(
                frame,
                (box["x1"], box["y1"]),
                (box["x2"], box["y2"]),
                color,
                2,
            )
            cv2.putText(
                frame,
                str(index + 1),
                (box["x1"] + 4, max(14, box["y1"] + 16)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1,
                cv2.LINE_AA,
            )

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return ImageOps.contain(Image.fromarray(rgb), size, Image.LANCZOS)


def _bgr(hex_color):
    value = str(hex_color).lstrip("#")
    red, green, blue = (int(value[index:index + 2], 16) for index in (0, 2, 4))
    return (blue, green, red)


_BGR_COLORS = tuple(_bgr(color) for color in ROI_COLORS)


def roi_hex(index):
    """Cor do ROI na interface, pela posição (mesma dos overlays)."""
    return ROI_COLORS[index % len(ROI_COLORS)]


def status_color(ok):
    """Cor do texto do resultado: verde quando aprovado, vermelho quando não."""
    return SUCCESS if ok else DANGER


def failing_names(details):
    """Nomes dos ROIs que reprovaram de fato (têm % de acerto calculado)."""
    names = []
    for entry in details or []:
        if not isinstance(entry, dict):
            continue
        if entry.get("ok") is False and isinstance(entry.get("match"), (int, float)):
            names.append(str(entry.get("name") or "ROI"))
    return names


def display_result(record):
    """Texto do resultado sempre coerente com os ROIs gravados na captura.

    Registros antigos guardaram apenas o primeiro ROI reprovado; aqui o texto é
    recalculado a partir dos detalhes, então todas as falhas aparecem.
    """
    failed = failing_names(getattr(record, "details", None))
    if failed and not getattr(record, "ok", True):
        return "ERRO: " + " + ".join(name.upper() for name in failed)
    return record.result


class AnalysisDialog:
    """Mostra a captura analisada com o resultado e o % de cada ROI."""

    def __init__(self, parent, record):
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
            display_result(record),
            kind="header",
            bg=CARD,
            fg=status_color(record.ok),
        ).pack(side="left")
        ui.label(
            header,
            f"{record.time_text} · {record.recipe}",
            kind="small",
            bg=CARD,
        ).pack(side="left", padx=(12, 0))

        image = record_image(record, (PREVIEW_WIDTH, PREVIEW_HEIGHT), overlay=True)
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
        ui.label(
            metrics, "ROIs desta captura", kind="small", bg=CARD, fg=TEXT_DIM
        ).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 4))

        details = [entry for entry in (record.details or []) if isinstance(entry, dict)]
        if not details:
            ui.label(
                metrics,
                "Captura sem métricas por ROI (histórico anterior a esta versão).",
                kind="small",
                bg=CARD,
            ).grid(row=1, column=0, columnspan=4, sticky="w")
        for position, entry in enumerate(details, start=1):
            ok = entry.get("ok")
            match = entry.get("match")
            name_color = roi_hex(position - 1)
            value_color = SUCCESS if ok else (DANGER if ok is False else TEXT_DIM)
            window = ""
            if isinstance(entry.get("min"), (int, float)) and isinstance(entry.get("max"), (int, float)):
                window = f"janela {entry['min']:g}–{entry['max']:g}%"
            ui.label(
                metrics,
                f"{position} · {entry.get('name') or 'ROI'}",
                kind="bold",
                bg=CARD,
                fg=name_color,
            ).grid(row=position, column=0, sticky="w", padx=(0, 10), pady=1)
            ui.label(
                metrics,
                f"{match:.1f}%" if isinstance(match, (int, float)) else "—",
                kind="bold",
                bg=CARD,
                fg=value_color,
            ).grid(row=position, column=1, sticky="w", pady=1)
            ui.label(metrics, window, kind="small", bg=CARD).grid(
                row=position, column=2, sticky="w", padx=(10, 20), pady=1
            )
            ui.label(
                metrics,
                "APROVADO" if ok else ("REPROVADO" if ok is False else "—"),
                kind="small",
                bg=CARD,
                fg=value_color,
            ).grid(row=position, column=3, sticky="w", pady=1)

        footer = ctk.CTkFrame(card, fg_color=CARD, corner_radius=0)
        footer.pack(fill="x", padx=16, pady=(4, 14))
        ui.label(
            footer, f"Tempo de análise: {record.elapsed_ms} ms", kind="small", bg=CARD
        ).pack(side="left")
        ui.button(
            footer,
            "Fechar",
            command=self.window.destroy,
            variant="secondary",
            size="md",
        ).pack(side="right")

        self.window.bind("<Escape>", lambda _event: self.window.destroy())
        self.window.update_idletasks()
        width = max(self.window.winfo_reqwidth(), 520)
        height = self.window.winfo_reqheight()
        x = parent.winfo_rootx() + max(0, (parent.winfo_width() - width) // 2)
        y = parent.winfo_rooty() + max(0, (parent.winfo_height() - height) // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        self.window.grab_set()
