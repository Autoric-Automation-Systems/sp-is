import tkinter as tk
from components.layout import BaseLayout
from styles.theme import *

class UsersView:
    def __init__(self, parent, app):
        layout = BaseLayout(parent, app)

        tk.Label(layout.content, text="GESTÃO DE USUÁRIOS", font=FONT_TITLE, fg=TEXT, bg=BG).pack(pady=50)