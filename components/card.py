import tkinter as tk
from styles.theme import CARD, BORDER

class Card:
    def __init__(self, parent, width=760):
        self.frame = tk.Frame(
            parent,
            bg=CARD,
            width=width,
            highlightthickness=2,
            highlightbackground=BORDER,
            bd=0
        )
        self.frame.pack(fill="both", expand=True, pady=32)
        self.frame.pack_propagate(False)
        self.content = tk.Frame(self.frame, bg=CARD)
        self.content.pack(fill="both", expand=True, padx=32, pady=32)