import tkinter as tk
from styles.theme import CARD, BORDER

class Card:
    def __init__(self, parent, width=760):
        self.frame = tk.Frame(
            parent,
            bg=CARD,
            width=width,
            highlightthickness=1,
            highlightbackground=BORDER
        )

        self.frame.place(relx=0.5, rely=0.5, anchor="center")
        self.frame.pack_propagate(True)  # Permite crescer conforme o conteúdo

        self.content = tk.Frame(self.frame, bg=CARD)
        self.content.pack(fill="both", expand=True, padx=20, pady=20)