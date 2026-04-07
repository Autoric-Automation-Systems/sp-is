import os
import tkinter as tk
from PIL import Image, ImageTk
from styles.theme import *

BG = HEADER_BG

LOGO_PATH = "assets/logo.png"

class Header:
    def __init__(self, parent, app):
        self.frame = tk.Frame(parent, bg=BG, height=100)
        self.frame.pack(fill="x")
        self.frame.pack_propagate(False)

        # -------- LOGO --------
        try:
            img = Image.open(LOGO_PATH)
            img = img.resize((180, 80))  # Tamanho mais proporcional
            self.logo = ImageTk.PhotoImage(img)

            lbl = tk.Label(self.frame, image=self.logo, bg=BG)
            lbl.image = self.logo
            lbl.pack(side="left", padx=(24, 12), pady=10)
        except Exception as e:
            print("Erro ao carregar imagem:", e)

        # -------- TÍTULO --------
        title = tk.Label(
            self.frame,
            text="Smart Plant - Inspection System",
            font=FONT_TITLE,
            fg=TEXT,
            bg=BG,
            anchor="w"
        )
        title.pack(side="left", padx=10, pady=10, fill="y", expand=True)

        # -------- LINHA INFERIOR --------
        tk.Frame(self.frame, bg=BORDER, height=2).pack(fill="x", side="bottom", pady=(0, 0))