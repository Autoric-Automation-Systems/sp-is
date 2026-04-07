import tkinter as tk
from components.header import Header
from components.footer import Footer
from styles.theme import *

class BaseLayout:
    def __init__(self, parent, app):
        self.frame = tk.Frame(parent, bg=BG)
        self.frame.pack(fill="both", expand=True)
        self.frame.pack_propagate(False)
        Header(self.frame, app)
        self.content = tk.Frame(self.frame, bg=BG)
        self.content.pack(fill="both", expand=True, padx=0, pady=0)
        Footer(self.frame, app)