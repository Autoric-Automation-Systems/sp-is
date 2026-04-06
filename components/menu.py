import tkinter as tk

class Menu:
    def __init__(self, parent, app):
        self.app = app

        self.window = tk.Toplevel(parent)
        self.window.title("Menu")
        
        screen_height = self.window.winfo_screenheight()
        self.window.geometry(f"220x300+0+{screen_height-320}")        
        tk.Button(self.window, text="Produção",
                  command=lambda: self.go("production")).pack(fill="x")

        tk.Button(self.window, text="Receitas",
                  command=lambda: self.go("recipes")).pack(fill="x")

        tk.Button(self.window, text="Usuários",
                  command=lambda: self.go("users")).pack(fill="x")

        tk.Button(self.window, text="Diagnóstico",
                  command=lambda: self.go("diagnosis")).pack(fill="x")

        tk.Button(self.window, text="Logout",
                  command=lambda: self.go("logout")).pack(fill="x")

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

        elif target == "logout":
            self.app.current_user = None
            self.app.show_login()