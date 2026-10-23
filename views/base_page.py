"""Página persistente do shell da aplicação."""
import customtkinter as ctk

from components.camera_view import get_camera
from styles.theme import BG


class Page(ctk.CTkFrame):
    """Frame reutilizado entre navegações; só é construído uma vez."""

    route = ""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color=BG, corner_radius=0)
        self.app = app
        self.running = False
        self.build()

    @property
    def camera(self):
        """Sempre a câmera em uso: reflete trocas feitas em Configurações."""
        return get_camera()

    def build(self):
        """Constrói a interface (chamado uma única vez)."""

    def on_show(self):
        """Chamado sempre que a página fica visível."""

    def on_hide(self):
        """Chamado ao trocar de página; deve parar loops/timers."""

    def on_close(self):
        self.on_hide()
