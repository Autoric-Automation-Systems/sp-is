import os
import tkinter as tk
from styles.theme import *
from PIL import Image, ImageTk

LOGODEV_PATH = "assets/logo-dev.png"
LOGO_PATH = "assets/logo.png"

class LoginView:
    def __init__(self, parent, app):
        self.app = app
        frame = tk.Frame(
            parent,
            bg=BG,
            padx=40,
            pady=40,
            relief="flat",
            bd=0,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        frame.place(relx=0.5, rely=0.5, anchor="center")

        # -------- LOGO --------
        try:
            img = Image.open(LOGO_PATH)
            img = img.resize((420, 180))
            self.logo = ImageTk.PhotoImage(img)
            tk.Label(frame, image=self.logo, bg=BG).pack(pady=(0, 18))
        except Exception as e:
            print("Erro ao carregar imagem:", e)

        # Título
        tk.Label(frame, text="LOGIN", font=FONT_TITLE, fg=TEXT, bg=BG).pack(pady=(0, 18))

        # Login form
        entry_opts = {
            "bg": INPUT_BG,
            "fg": TEXT,
            "insertbackground": TEXT,
            "font": FONT,
            "relief": "flat",
            "highlightthickness": 1,
            "highlightbackground": INPUT_BORDER,
            "highlightcolor": INPUT_FOCUS,
            "width": 28,
            "justify": "center"
        }

        self.user = tk.Entry(frame, **entry_opts)
        self.user.pack(pady=6)
        self.user.insert(0, "admin")

        self.password = tk.Entry(frame, show="*", **entry_opts)
        self.password.pack(pady=6)
        self.password.insert(0, "admin")

        self.msg = tk.Label(frame, text="", fg=DANGER, bg=BG, font=FONT)
        self.msg.pack(pady=(2, 8))

        tk.Button(
            frame,
            text="Entrar",
            command=self.login,
            bg=BUTTON_BG,
            fg=BUTTON_TEXT,
            font=BUTTON_FONT,
            activebackground=BUTTON_ACTIVE,
            activeforeground=BUTTON_TEXT,
            relief="flat",
            bd=0,
            highlightthickness=0,
            cursor="hand2",
            width=18,
            pady=6
        ).pack(pady=(0, 18))

        # -------- LOGO DEV --------
        try:
            img = Image.open(LOGODEV_PATH)
            img = img.resize((180, 48))
            self.logodev = ImageTk.PhotoImage(img)
            tk.Label(frame, image=self.logodev, bg=BG).pack(pady=(0, 2))
        except Exception as e:
            print("Erro ao carregar imagem:", e)

        # Sub-Title
        tk.Label(frame, text="www.autoric.com.br", font=FONT_SMALL, fg=TEXT_DIM, bg=BG).pack(pady=(0, 2))

    def login(self):
        if self.user.get() == "admin" and self.password.get() == "admin":
            self.app.current_user = "admin"
            self.app.show_production()
        else:
            self.msg.config(text="Usuário ou senha inválidos")