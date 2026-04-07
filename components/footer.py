import tkinter as tk
import time
from components.menu import Menu
from styles.theme import *

BG = FOOTER_BG
BTN_BG = BUTTON_BG
BTN_HOVER = BUTTON_HOVER
BTN_TEXT = BUTTON_TEXT

class Footer:
    def __init__(self, parent, app):
        self.app = app

        self.frame = tk.Frame(
            parent,
            height=40,
            bg=BG,
            relief="flat",
            bd=0,
            highlightthickness=0,
            padx=10,
            pady=5
        )
        self.frame.pack(fill="x", side="bottom")
        self.frame.pack_propagate(False)

        # BOTÃO MENU
        tk.Button(
            self.frame,
            text="☰ MENU",
            command=self.open_menu,
            font=BUTTON_FONT,
            bg=BTN_BG,
            fg=BTN_TEXT,
            relief="flat",
            bd=0,
            padx=12,
            pady=5,
            activebackground=BTN_HOVER,
            activeforeground=BTN_TEXT,
            cursor="hand2",
            highlightthickness=0
        ).pack(side="left", padx=10)

        # INFO DIREITA
        self.info = tk.Label(
            self.frame,
            fg=BTN_TEXT,
            bg=BG,
            font=FONT_SMALL,
            anchor="e"
        )
        self.info.pack(side="right", padx=10)

        self.update_time()

    def update_time(self):
        now = time.strftime("%H:%M:%S")
        user = self.app.current_user or "-"
        self.info.config(text=f"{user} | {now}")
        self.frame.after(1000, self.update_time)

    def open_menu(self):
        Menu(self.frame, self.app)