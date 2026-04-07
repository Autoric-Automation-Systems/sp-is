import tkinter as tk
from components.header import Header
from components.footer import Footer
from styles.theme import *

class BaseLayout:
    def __init__(self, parent, app):
        # FRAME ROOT
        self.frame = tk.Frame(parent, bg=BG)
        self.frame.pack(fill="both", expand=True)
        self.frame.pack_propagate(False)

        # HEADER
        Header(self.frame, app)

        # CONTENT (área central, estilizada)
        self.content = tk.Frame(self.frame, bg=BG)
        self.content.pack(fill="both", expand=True, padx=0, pady=0)

        # FOOTER
        Footer(self.frame, app)