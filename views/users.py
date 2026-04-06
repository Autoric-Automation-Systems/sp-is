import tkinter as tk
from components.layout import BaseLayout

class UsersView:
    def __init__(self, parent, app):
        layout = BaseLayout(parent, app)

        tk.Label(layout.content, text="GESTÃO DE USUÁRIOS").pack(pady=50)