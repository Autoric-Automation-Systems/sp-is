import tkinter as tk
import time
from components.menu import Menu

class Footer:
    def __init__(self, parent, app):
        self.app = app

        self.frame = tk.Frame(parent, height=40, bg="#333")
        self.frame.pack(fill="x", side="bottom")
        self.frame.pack_propagate(False)

        tk.Button(self.frame, text="☰ MENU", command=self.open_menu).pack(side="left", padx=10)

        self.info = tk.Label(self.frame, fg="white", bg="#333")
        self.info.pack(side="right", padx=10)

        self.update_time()

    def update_time(self):
        now = time.strftime("%H:%M:%S")
        user = self.app.current_user or "-"
        self.info.config(text=f"{now} | {user}")
        self.frame.after(1000, self.update_time)

    def open_menu(self):
        Menu(self.frame, self.app)