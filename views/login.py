import tkinter as tk

class LoginView:
    def __init__(self, parent, app):
        self.app = app
        frame = tk.Frame(parent)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="SP-IS LOGIN", font=("Arial", 20)).pack(pady=20)

        self.user = tk.Entry(frame)
        self.user.pack(pady=5)
        self.user.insert(0, "admin")

        self.password = tk.Entry(frame, show="*")
        self.password.pack(pady=5)
        self.password.insert(0, "admin")

        self.msg = tk.Label(frame, text="", fg="red")
        self.msg.pack()

        tk.Button(frame, text="Entrar", command=self.login).pack(pady=10)

    def login(self):
        if self.user.get() == "admin" and self.password.get() == "admin":
            self.app.current_user = "admin"
            self.app.show_production()
        else:
            self.msg.config(text="Usuário ou senha inválidos")