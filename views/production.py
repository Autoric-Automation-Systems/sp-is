import tkinter as tk
from components.layout import BaseLayout

class ProductionView:
    def __init__(self, parent, app):
        layout = BaseLayout(parent, app)

        recipe = app.current_recipe or "⚠️ SEM RECEITA ATIVA"

        tk.Label(layout.content, text=f"Receita: {recipe}").pack(pady=10)
        tk.Label(layout.content, text="(Câmera aqui)").pack()