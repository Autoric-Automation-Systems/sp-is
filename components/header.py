import tkinter as tk

class Header:
    def __init__(self, parent, app):
        frame = tk.Frame(parent, height=50, bg="#333")
        frame.pack(fill="x", side="top")
        frame.pack_propagate(False)

        recipe = app.current_recipe or "SEM RECEITA"

        tk.Label(frame, text="SP-IS", fg="white", bg="#333").pack(side="left", padx=10)
        tk.Label(frame, text=f"Receita: {recipe}", fg="white", bg="#333").pack(side="right", padx=10)