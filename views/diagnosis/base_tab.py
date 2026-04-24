"""Classe base para as abas de diagnóstico"""
import tkinter as tk
from styles.theme import *


class BaseTab:
    """Fornece helpers para construção de abas"""

    def __init__(self, parent):
        self.parent = parent
        self.container = tk.Frame(parent, bg=CARD)
        self.container.pack(fill="both", expand=True, padx=24, pady=24)

    def _make_label_frame(self, parent, titulo, **kwargs):
        """Cria um LabelFrame padronizado"""
        fg = kwargs.pop("fg", PRIMARY)
        frame = tk.LabelFrame(
            parent,
            text=titulo,
            font=FONT_HEADER,
            fg=fg,
            bg=CARD,
            bd=0,
            padx=16,
            pady=12,
        )
        if "pack" not in kwargs:
            frame.pack(fill="x", pady=(0, 16))
        return frame

    def _make_info_table(self, parent, data, **kwargs):
        """Cria tabela label: valor"""
        start_row = kwargs.pop("start_row", 0)
        for i, (label, value) in enumerate(data):
            tk.Label(
                parent, text=f"{label}:", font=FONT_BOLD, fg=TEXT_DIM, bg=CARD
            ).grid(row=start_row + i, column=0, sticky="w", pady=3)
            tk.Label(
                parent, text=value, font=FONT, fg=TEXT, bg=CARD
            ).grid(row=start_row + i, column=1, sticky="w", padx=(12, 0), pady=3)

    def _make_bar(self, parent, **kwargs):
        """Cria uma barra de progresso via Canvas"""
        height = kwargs.pop("height", 20)
        bg_color = kwargs.pop("bg_color", INPUT_BG)
        fill_color = kwargs.pop("fill_color", SUCCESS)
        canvas = tk.Canvas(
            parent,
            height=height,
            bg=bg_color,
            highlightthickness=1,
            highlightbackground=BORDER,
            bd=0,
        )
        canvas.pack(fill="x", pady=(0, 8))
        fill_rect = canvas.create_rectangle(0, 0, 0, height, fill=fill_color, width=0)
        return canvas, fill_rect

    def _make_header_text(self, parent, text, font_size=32, **kwargs):
        """Label grande para percentual"""
        fg = kwargs.pop("fg", SUCCESS)
        lbl = tk.Label(
            parent, text=text, font=("Segoe UI", font_size, "bold"), fg=fg, bg=CARD
        )
        lbl.pack(pady=10)
        return lbl
