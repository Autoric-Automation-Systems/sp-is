"""Menu lateral persistente de navegação."""
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


class Sidebar:
    def __init__(self, parent, app):
        self.app = app
        self.frame = ctk.CTkFrame(
            parent, fg_color=SIDEBAR_BG, corner_radius=0, width=SIDEBAR_WIDTH
        )
        self.frame.grid_propagate(False)

        header = ctk.CTkFrame(self.frame, fg_color=SIDEBAR_BG, corner_radius=0)
        header.pack(fill="x", padx=18, pady=(16, 10))
        ui.label(header, "SP-IS", kind="header", bg=SIDEBAR_BG).pack(anchor="w")
        ui.label(
            header, "SMART PLANT · INSPECTION", kind="small", bg=SIDEBAR_BG
        ).pack(anchor="w")

        ctk.CTkFrame(self.frame, fg_color=BORDER, height=1, corner_radius=0).pack(
            fill="x", padx=14, pady=(0, 8)
        )

        self.nav_container = ctk.CTkFrame(self.frame, fg_color=SIDEBAR_BG, corner_radius=0)
        self.nav_container.pack(fill="x")

        self.user_container = ctk.CTkFrame(
            self.frame, fg_color=SIDEBAR_BG, corner_radius=0
        )
        self.user_container.pack(fill="x", side="bottom")

        ctk.CTkFrame(self.frame, fg_color=BORDER, height=1, corner_radius=0).pack(
            fill="x", padx=14, pady=8, side="bottom"
        )

        ctk.CTkFrame(self.frame, fg_color=SIDEBAR_BG, corner_radius=0).pack(
            fill="both", expand=True
        )

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

        for key, text in NAV_ITEMS:
            self._nav_button(key, text, key == route)

    def _nav_button(self, key, text, active):
        button = ctk.CTkButton(
            self.nav_container,
            text=text,
            anchor="w",
            command=lambda: self.app.show_route(key),
            height=38,
            corner_radius=8,
            font=ui.font("Segoe UI", 13, "bold" if active else "normal"),
            fg_color=BUTTON_BG if active else "transparent",
            hover_color=BUTTON_HOVER,
            text_color=PRIMARY if active else TEXT_DIM,
        )
        button.pack(fill="x", padx=12, pady=1)

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
                size="sm",
            ).pack(fill="x", padx=14, pady=(0, 12))
        else:
            ui.label(
                self.user_container, "Visitante", kind="small", bg=SIDEBAR_BG
            ).pack(anchor="w", padx=18, pady=(2, 6))
            ui.button(
                self.user_container,
                "Entrar",
                command=self.app.login,
                variant="primary",
                size="sm",
            ).pack(fill="x", padx=14, pady=(0, 12))
