"""Classe base para as abas de diagnóstico."""
import time

import customtkinter as ctk

from components import ui
from styles.theme import *


class BaseTab:
    """Fornece helpers para construção de abas."""

    def __init__(self, parent):
        self.parent = parent
        self._cache = {}
        self.container = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=0)
        self.container.pack(fill="both", expand=True, padx=18, pady=16)

    def _cached(self, key, ttl, factory):
        """Evita repetir chamadas caras (subprocessos) em cada atualização."""
        now = time.monotonic()
        cached = self._cache.get(key)
        if cached is not None and now - cached[0] < ttl:
            return cached[1]
        value = factory()
        self._cache[key] = (now, value)
        return value

    def _section(self, parent, titulo, fg=PRIMARY, **kwargs):
        """Cartão com título; retorna o frame de conteúdo."""
        kwargs.pop("pack", None)
        card = ctk.CTkFrame(
            parent,
            fg_color=CARD,
            corner_radius=8,
            border_width=1,
            border_color=BORDER,
        )
        card.pack(fill="x", pady=(0, 10))

        ui.label(card, titulo, kind="bold", fg=fg, bg=CARD).pack(
            anchor="w", padx=12, pady=(10, 4)
        )
        content = ctk.CTkFrame(card, fg_color=CARD, corner_radius=0)
        content.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        return content

    # Compatibilidade com as abas existentes.
    _make_label_frame = _section

    def _make_info_table(self, parent, data, **kwargs):
        """Cria tabela label: valor."""
        start_row = kwargs.pop("start_row", 0)
        for i, (label_text, value) in enumerate(data):
            ui.label(parent, f"{label_text}:", kind="small", bg=CARD).grid(
                row=start_row + i, column=0, sticky="w", pady=2
            )
            ui.label(parent, value, kind="body", bg=CARD).grid(
                row=start_row + i, column=1, sticky="w", padx=(12, 0), pady=2
            )

    def _make_bar(self, parent, **kwargs):
        """Cria uma barra de progresso via Canvas."""
        height = kwargs.pop("height", 18)
        bg_color = kwargs.pop("bg_color", INPUT_BG)
        fill_color = kwargs.pop("fill_color", SUCCESS)
        holder = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=0)
        holder.pack(fill="x", pady=(0, 8))
        canvas = ui.canvas(holder, width=200, height=height, bg=bg_color)
        canvas.configure(height=height, highlightthickness=1,
                         highlightbackground=BORDER)
        canvas.pack(fill="x")
        fill_rect = canvas.create_rectangle(0, 0, 0, height, fill=fill_color, width=0)
        return canvas, fill_rect

    def _make_header_text(self, parent, text, font_size=32, **kwargs):
        """Label grande para percentual."""
        fg = kwargs.pop("fg", SUCCESS)
        lbl = ctk.CTkLabel(
            parent,
            text=text,
            font=ui.font("Segoe UI", int(font_size * 0.7), "bold"),
            text_color=fg,
            fg_color=CARD,
        )
        lbl.pack(pady=8)
        return lbl
