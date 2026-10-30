import logging
import tkinter as tk

import customtkinter as ctk
from PIL import Image

from components import ui
from paths import ASSETS_DIR
from services.recipe_service import list_recipes
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
    """Header persistente: logo, título, receita em uso e resumo de estatísticas."""

    def __init__(self, parent, app):
        self.app = app
        self._recipes = {}
        self.frame = ctk.CTkFrame(parent, fg_color=BG, corner_radius=0, height=96)
        self.frame.pack_propagate(False)

        try:
            image = Image.open(LOGO_PATH)
            self.logo = ctk.CTkImage(light_image=image, dark_image=image, size=(150, 66))
            ctk.CTkLabel(self.frame, image=self.logo, text="", fg_color=BG).pack(
                side="left", padx=(20, 8), pady=8
            )
        except Exception as exc:
            LOGGER.warning("Erro ao carregar imagem: %s", exc)

        ui.label(
            self.frame, "Smart Plant - Inspection System", kind="header", bg=BG
        ).pack(side="left", padx=(4, 0), pady=8)

        self._build_recipe()
        self._build_stats()

        ctk.CTkFrame(self.frame, fg_color=BORDER, height=1, corner_radius=0).pack(
            fill="x", side="bottom"
        )

    # ------------------------------------------------------------------ receita
    def _build_recipe(self):
        panel = ctk.CTkFrame(self.frame, fg_color=BG, corner_radius=0)
        panel.pack(side="left", padx=(22, 0), pady=10)

        ui.label(panel, "RECEITA EM USO", kind="small", bg=BG).pack(anchor="w")
        row = ctk.CTkFrame(panel, fg_color=BG, corner_radius=0)
        row.pack(anchor="w", pady=(2, 0))

        self.recipe_var = tk.StringVar()
        self.recipe_combo = ui.dropdown(
            row,
            self.recipe_var,
            [],
            width=14,
            command=self._on_recipe_selected,
        )
        self.recipe_combo.pack(side="left")
        ui.button(row, "Usar", command=self._apply_recipe, size="sm").pack(
            side="left", padx=(6, 0)
        )

    def refresh_recipe(self):
        """Recarrega a lista de receitas e marca a que está em uso."""
        try:
            recipes = list_recipes()
        except Exception:
            LOGGER.exception("Falha ao listar receitas no header")
            recipes = []

        self._recipes = {recipe["name"]: recipe for recipe in recipes}
        names = sorted(self._recipes, key=str.lower)
        self.recipe_combo.configure(values=names or ["(nenhuma)"])

        current = (self.app.current_recipe or {}).get("name", "")
        if current in self._recipes:
            self.recipe_var.set(current)
        elif names:
            self.recipe_var.set(names[0])
        else:
            self.recipe_var.set("(nenhuma)")

    def _on_recipe_selected(self, name):
        recipe = self._recipes.get(name)
        if recipe is not None and recipe is not self.app.current_recipe:
            self.app.set_active_recipe(recipe)

    def _apply_recipe(self):
        recipe = self._recipes.get(self.recipe_var.get())
        if recipe is not None:
            self.app.set_active_recipe(recipe)

    # ------------------------------------------------------------------ stats
    def _build_stats(self):
        stats_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        stats_frame.pack(side="right", padx=(8, 16))

        self.values = {}
        for key, title, color in STAT_ITEMS:
            block = ctk.CTkFrame(
                stats_frame,
                fg_color=HEADER_BG,
                corner_radius=8,
                border_width=1,
                border_color=BORDER,
                width=88,
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
                font=ui.font(size=17, weight="bold"),
                text_color=color,
                fg_color=HEADER_BG,
                anchor="w",
            )
            value.pack(anchor="w", padx=9, pady=(0, 4))
            self.values[key] = value

    def update_stats(self, stats):
        self.values["total"].configure(text=str(stats["total"]))
        self.values["ok"].configure(text=str(stats["ok"]))
        self.values["nok"].configure(text=str(stats["nok"]))
        self.values["rate"].configure(
            text=f'{stats["approval"]:.1f}%',
            text_color=SUCCESS if stats["approval"] >= 90 else WARNING,
        )
        self.values["avg"].configure(text=f'{stats["avg_ms"]:.0f} ms')
