import tkinter as tk
from views.login import LoginView
from views.production import ProductionView
from views.users import UsersView
from views.recipes import RecipesView
from views.diagnosis_view import DiagnosisView

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.configure(bg="#1e1e1e")
        self.title("SP-IS")
        self.update_idletasks()
        self.attributes("-zoomed", True)   
        self.attributes("-fullscreen", True)     
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.current_user = None
        self.current_recipe = None

        self.container = tk.Frame(self)
        self.container.pack(fill="both", expand=True)

        self.show_login()

    def clear(self):
        for widget in self.container.winfo_children():
            if hasattr(widget, "cleanup"):
                widget.cleanup()
            widget.destroy()

    def show_login(self):
        self.clear()
        LoginView(self.container, self)

    def show_production(self):
        self.clear()
        ProductionView(self.container, self)

    def show_users(self):
        self.clear()
        UsersView(self.container, self)

    def show_recipes(self):
        self.clear()
        RecipesView(self.container, self)

    def show_diagnosis(self):
        self.clear()
        DiagnosisView(self.container, self)

    def on_close(self):
        if self.current_user is None:
            self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()