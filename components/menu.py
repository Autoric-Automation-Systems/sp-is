import tkinter as tk
from styles.theme import *

class Menu:
    def __init__(self, parent, app):
        self.app = app

        self.window = tk.Toplevel(parent)
        #self.window.title("Menu")
        self.window.configure(bg=HEADER_BG)

        screen_height = self.window.winfo_screenheight()
        self.window.geometry(f"240x340+0+{screen_height-360}")
        self.window.resizable(False, False)

        tk.Label(
            self.window,
            text="MENU",
            font=FONT_HEADER,
            fg=TEXT,
            bg=HEADER_BG,
            pady=16
        ).pack(fill="x")

        btn_opts = {
            "font": BUTTON_FONT,
            "bg": BUTTON_BG,
            "fg": BUTTON_TEXT,
            "activebackground": BUTTON_ACTIVE,
            "activeforeground": BUTTON_TEXT,
            "relief": "flat",
            "bd": 0,
            "highlightthickness": 0,
            "cursor": "hand2",
            "padx": 10,
            "pady": 10
        }

        tk.Button(self.window, text="Produção",
                  command=lambda: self.go("production"), **btn_opts).pack(fill="x", pady=(0, 2))
        tk.Button(self.window, text="Receitas",
                  command=lambda: self.go("recipes"), **btn_opts).pack(fill="x", pady=2)
        tk.Button(self.window, text="Usuários",
                  command=lambda: self.go("users"), **btn_opts).pack(fill="x", pady=2)
        tk.Button(self.window, text="Diagnóstico",
              command=lambda: self.go("diagnosis"), **btn_opts).pack(fill="x", pady=2)
        tk.Button(self.window, text="Configurações",
              command=lambda: self.go("config"), **btn_opts).pack(fill="x", pady=(16, 2))
        logout_opts = btn_opts.copy()
        logout_opts["bg"] = DANGER
        logout_opts["activebackground"] = DANGER_HOVER
        tk.Button(self.window, text="Logout",
              command=lambda: self.go("logout"),
              **logout_opts).pack(fill="x", pady=(16, 0))

    def go(self, target):
        self.window.destroy()

        if target == "production":
            self.app.show_production()
        elif target == "users":
            self.app.show_users()
        elif target == "recipes":
            self.app.show_recipes()
        elif target == "diagnosis":
            self.app.show_diagnosis()
        elif target == "config":
            from views.config import ConfigView
            # Usa o root principal para evitar erro de janela destruída
            root = self.window.master if hasattr(self.window, 'master') else self.window
            ConfigView(root, self.app)
        elif target == "logout":
            self.app.current_user = None
            self.app.show_login()