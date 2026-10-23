"""Diálogo de login (a aplicação inicia em modo visitante)."""
import logging
import os

import customtkinter as ctk
from PIL import Image

from components import ui
from paths import ASSETS_DIR
from styles.theme import *

LOGGER = logging.getLogger(__name__)

LOGODEV_PATH = ASSETS_DIR / "logo-dev.png"
LOGO_PATH = ASSETS_DIR / "logo.png"

ADMIN_USER = os.environ.get("SPIS_ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("SPIS_ADMIN_PASSWORD", "admin")


class LoginDialog:
    def __init__(self, parent, app, next_route=None):
        self.app = app
        self.next_route = next_route

        self.window = ctk.CTkToplevel(parent)
        self.window.title("Entrar")
        self.window.configure(fg_color=BG)
        self.window.transient(parent)
        self.window.resizable(False, False)

        frame = ctk.CTkFrame(
            self.window, fg_color=CARD, corner_radius=10, border_width=1,
            border_color=BORDER,
        )
        frame.pack(fill="both", expand=True, padx=8, pady=8)

        try:
            image = Image.open(LOGO_PATH)
            self.logo = ctk.CTkImage(light_image=image, dark_image=image, size=(280, 120))
            ctk.CTkLabel(frame, image=self.logo, text="", fg_color=CARD).pack(pady=(6, 8))
        except Exception as exc:
            LOGGER.warning("Erro ao carregar imagem: %s", exc)

        ui.label(frame, "ENTRAR", kind="header", bg=CARD).pack(pady=(0, 12))

        ui.label(frame, "Usuário", kind="small", bg=CARD).pack(anchor="w", padx=26)
        self.user = ui.entry(frame, width=24, justify="left")
        self.user.pack(fill="x", padx=26, pady=(2, 8))
        self.user.insert(0, "admin")

        ui.label(frame, "Senha", kind="small", bg=CARD).pack(anchor="w", padx=26)
        self.password = ui.entry(frame, width=24, justify="left", show="*")
        self.password.pack(fill="x", padx=26, pady=(2, 8))
        self.password.insert(0, "admin")

        self.msg = ui.label(frame, "", kind="small", bg=CARD, fg=DANGER)
        self.msg.pack(pady=(0, 6))

        ui.button(
            frame, "Entrar", command=self.login, variant="primary", size="lg"
        ).pack(fill="x", padx=26, pady=(0, 6))
        ui.button(
            frame, "Cancelar", command=self.close, variant="secondary", size="md"
        ).pack(fill="x", padx=26)

        try:
            image = Image.open(LOGODEV_PATH)
            self.logodev = ctk.CTkImage(light_image=image, dark_image=image, size=(140, 38))
            ctk.CTkLabel(frame, image=self.logodev, text="", fg_color=CARD).pack(pady=(12, 8))
        except Exception as exc:
            LOGGER.warning("Erro ao carregar imagem: %s", exc)

        self.window.bind("<Return>", lambda _event: self.login())
        self.window.bind("<Escape>", lambda _event: self.close())

        self.window.update_idletasks()
        width, height = 420, self.window.winfo_reqheight()
        x = parent.winfo_rootx() + max(0, (parent.winfo_width() - width) // 2)
        y = parent.winfo_rooty() + max(0, (parent.winfo_height() - height) // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        self.window.grab_set()
        self.user.focus_set()

    def login(self):
        if self.user.get() == ADMIN_USER and self.password.get() == ADMIN_PASSWORD:
            self.app.current_user = "admin"
            next_route = self.next_route
            self.close()
            self.app.on_login(next_route)
        else:
            self.msg.configure(text="Usuário ou senha inválidos")

    def close(self):
        try:
            self.window.grab_release()
        except Exception:
            pass
        self.window.destroy()
