import tkinter as tk
from components.layout import BaseLayout
from styles.theme import *

class ProductionView:
    def __init__(self, parent, app):
        layout = BaseLayout(parent, app)

        recipe = app.current_recipe or "⚠️ SEM RECEITA ATIVA"

        tk.Label(layout.content, text=f"Receita: {recipe}", font=FONT, fg=TEXT, bg=BG).pack(pady=10)
        tk.Label(layout.content, text="(Câmera aqui)", font=FONT, fg=TEXT, bg=BG).pack()