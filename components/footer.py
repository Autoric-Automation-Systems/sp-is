import logging
import time

import customtkinter as ctk
from PIL import Image

from components import ui
from paths import ASSETS_DIR
from styles.theme import *

LOGGER = logging.getLogger(__name__)

BG = FOOTER_BG
LOGO_PATH = ASSETS_DIR / "logo-dev.png"


class Footer:
    """Footer persistente com logo dev, nome do sistema, usuário e relógio."""

    def __init__(self, parent, app):
        self.app = app
        self._after_id = None

        self.frame = ctk.CTkFrame(parent, fg_color=BG, corner_radius=0, height=46)
        self.frame.pack_propagate(False)

        try:
            image = Image.open(LOGO_PATH)
            self.logo = ctk.CTkImage(light_image=image, dark_image=image, size=(96, 26))
            ctk.CTkLabel(self.frame, image=self.logo, text="", fg_color=BG).pack(
                side="left", padx=(14, 10), pady=6
            )
        except Exception as exc:
            LOGGER.warning("Erro ao carregar logo dev: %s", exc)

        ui.label(self.frame, "SP-IS · Inspeção Visual", kind="small", bg=BG).pack(
            side="left"
        )

        self.info = ui.label(self.frame, "", kind="small", bg=BG)
        self.info.pack(side="right", padx=14)

        ctk.CTkFrame(self.frame, fg_color=BORDER, height=1, corner_radius=0).pack(
            fill="x", side="top"
        )

        self.update_time()

    def update_time(self):
        if not self.frame.winfo_exists():
            return
        now = time.strftime("%H:%M:%S")
        user = self.app.current_user or "visitante"
        self.info.configure(text=f"{user} | {now}")
        self._after_id = self.frame.after(1000, self.update_time)
