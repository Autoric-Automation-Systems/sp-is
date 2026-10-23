import logging

import customtkinter as ctk
from PIL import Image

from components import ui
from paths import ASSETS_DIR
from styles.theme import *

LOGGER = logging.getLogger(__name__)

BG = HEADER_BG
LOGO_PATH = ASSETS_DIR / "logo.png"

STAT_ITEMS = (
    ("total", "TOTAL", PRIMARY),
    ("ok", "OK", SUCCESS),
    ("nok", "NOK", DANGER),
    ("rate", "APROV.", WARNING),
    ("avg", "TEMPO", WARNING),
)


class Header:
    """Header persistente com logo, título e resumo global de estatísticas."""

    def __init__(self, parent, app):
        self.app = app
        self.frame = ctk.CTkFrame(parent, fg_color=BG, corner_radius=0, height=96)
        self.frame.pack_propagate(False)

        try:
            image = Image.open(LOGO_PATH)
            self.logo = ctk.CTkImage(light_image=image, dark_image=image, size=(168, 74))
            ctk.CTkLabel(self.frame, image=self.logo, text="", fg_color=BG).pack(
                side="left", padx=(22, 10), pady=8
            )
        except Exception as exc:
            LOGGER.warning("Erro ao carregar imagem: %s", exc)

        ui.label(
            self.frame, "Smart Plant - Inspection System", kind="title", bg=BG
        ).pack(side="left", padx=8, pady=8)

        stats_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        stats_frame.pack(side="right", padx=(8, 18))

        self.values = {}
        for key, title, color in STAT_ITEMS:
            block = ctk.CTkFrame(
                stats_frame,
                fg_color=HEADER_BG,
                corner_radius=8,
                border_width=1,
                border_color=BORDER,
                width=92,
                height=58,
            )
            block.pack(side="left", padx=3)
            block.pack_propagate(False)
            ui.label(block, title, kind="small", bg=HEADER_BG).pack(
                anchor="w", padx=9, pady=(6, 0)
            )
            value = ctk.CTkLabel(
                block,
                text="—",
                font=ui.font("Segoe UI", 17, "bold"),
                text_color=color,
                fg_color=HEADER_BG,
                anchor="w",
            )
            value.pack(anchor="w", padx=9, pady=(0, 4))
            self.values[key] = value

        ctk.CTkFrame(self.frame, fg_color=BORDER, height=1, corner_radius=0).pack(
            fill="x", side="bottom"
        )

    def update_stats(self, stats):
        self.values["total"].configure(text=str(stats["total"]))
        self.values["ok"].configure(text=str(stats["ok"]))
        self.values["nok"].configure(text=str(stats["nok"]))
        self.values["rate"].configure(
            text=f'{stats["approval"]:.1f}%',
            text_color=SUCCESS if stats["approval"] >= 90 else WARNING,
        )
        self.values["avg"].configure(text=f'{stats["avg_ms"]:.0f} ms')
