import tkinter as tk
from components.header import Header
from components.footer import Footer

class BaseLayout:
    def __init__(self, parent, app):
        self.frame = tk.Frame(parent)
        self.frame.pack(fill="both", expand=True)

        # HEADER (topo)
        self.header = Header(self.frame, app)

        # FOOTER (embaixo)
        self.footer = Footer(self.frame, app)

        # CONTENT (meio - SEMPRE depois dos dois)
        self.content = tk.Frame(self.frame)
        self.content.pack(fill="both", expand=True)