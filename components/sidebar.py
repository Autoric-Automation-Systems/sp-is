"""Menu lateral persistente de navegação.

Pensado para tela touch: botões altos, texto centralizado e distribuídos na
altura disponível, sem repetir a marca/informações que já aparecem no header.
"""

import customtkinter as ctk

from components import ui
from styles.theme import *

NAV_ITEMS = [
    ("main", "Principal"),
    ("recipes", "Receitas"),
    ("settings", "Configurações"),
    ("users", "Usuários"),
    ("diagnosis", "Diagnósticos"),
    ("help", "Ajuda"),
    ("about", "Sobre"),
]

NAV_BUTTON_HEIGHT = 58


class Sidebar:
    def __init__(self, parent, app):
        self.app = app
        self.frame = ctk.CTkFrame(
            parent, fg_color=SIDEBAR_BG, corner_radius=0, width=SIDEBAR_WIDTH
        )
        self.frame.grid_propagate(False)

        self.user_container = ctk.CTkFrame(
            self.frame, fg_color=SIDEBAR_BG, corner_radius=0
        )
        self.user_container.pack(fill="x", side="bottom")

        ctk.CTkFrame(self.frame, fg_color=BORDER, height=1, corner_radius=0).pack(
            fill="x", padx=14, pady=8, side="bottom"
        )

        self.nav_container = ctk.CTkFrame(self.frame, fg_color=SIDEBAR_BG, corner_radius=0)
        self.nav_container.pack(fill="both", expand=True, padx=6, pady=(12, 4))

        self.set_active("main")
        self.set_user(app.current_user)

    def show(self):
        self.frame.grid(row=0, column=0, sticky="nsew")

    def hide(self):
        self.frame.grid_remove()

    def set_active(self, route):
        if route == "recipe_edit":
            route = "recipes"
        for child in self.nav_container.winfo_children():
            child.destroy()

        for index, (key, text) in enumerate(NAV_ITEMS):
            # Peso igual por linha: os botões se distribuem na altura do menu.
            self.nav_container.grid_rowconfigure(index, weight=1, uniform="nav")
            self._nav_button(index, key, text, key == route)

    def _nav_button(self, row, key, text, active):
        """Botão estilo painel industrial: retangular, contornado e centralizado."""
        button = ctk.CTkButton(
            self.nav_container,
            text=text.upper(),
            anchor="center",
            command=lambda: self.app.show_route(key),
            height=NAV_BUTTON_HEIGHT,
            corner_radius=3,
            border_width=2,
            border_color=PRIMARY if active else BORDER,
            font=ui.font(size=14, weight="bold"),
            fg_color=BUTTON_BG if active else "transparent",
            hover_color=BUTTON_HOVER,
            text_color=PRIMARY if active else TEXT_DIM,
        )
        button.grid(row=row, column=0, sticky="nsew", padx=6, pady=3)

    def set_user(self, user):
        for child in self.user_container.winfo_children():
            child.destroy()

        if user:
            ui.label(
                self.user_container, f"Usuário: {user}", kind="small", bg=SIDEBAR_BG
            ).pack(anchor="w", padx=18, pady=(2, 6))
            ui.button(
                self.user_container,
                "Sair",
                command=self.app.logout,
                variant="danger",
                size="md",
            ).pack(fill="x", padx=12, pady=(0, 12), ipady=6)
        else:
            ui.label(
                self.user_container, "Visitante", kind="small", bg=SIDEBAR_BG
            ).pack(anchor="w", padx=18, pady=(2, 6))
            ui.button(
                self.user_container,
                "Entrar",
                command=self.app.login,
                variant="primary",
                size="md",
            ).pack(fill="x", padx=12, pady=(0, 12), ipady=6)
