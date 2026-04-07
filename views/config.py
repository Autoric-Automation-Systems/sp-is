import tkinter as tk
from tkinter import messagebox
from services.config_service import load_config, save_config
from styles.theme import *

class ConfigView:
    def __init__(self, parent, app):
        self.app = app
        self.config = load_config()

        self.window = tk.Toplevel(parent)
        self.window.title("Configurações")
        self.window.configure(bg=HEADER_BG)
        self.window.geometry("320x200")
        self.window.resizable(False, False)

        tk.Label(
            self.window,
            text="Configurações do Teste",
            font=FONT_HEADER,
            fg=TEXT,
            bg=HEADER_BG,
            pady=16
        ).pack(fill="x")

        frame = tk.Frame(self.window, bg=HEADER_BG)
        frame.pack(pady=16, padx=16, fill="x")

        tk.Label(frame, text="Threshold (sensibilidade)", bg=HEADER_BG, fg=TEXT, font=FONT).grid(row=0, column=0, sticky="w")
        self.threshold_var = tk.StringVar(value=str(self.config.get("threshold", 0.05)))
        tk.Entry(frame, textvariable=self.threshold_var, width=8, font=FONT, justify="center").grid(row=0, column=1, padx=8)

        tk.Button(
            self.window,
            text="Salvar",
            command=self.save,
            bg=SUCCESS,
            fg=TEXT,
            font=BUTTON_FONT,
            activebackground=SUCCESS,
            activeforeground=TEXT,
            relief="flat",
            width=12,
            bd=0,
            highlightthickness=0,
            cursor="hand2"
        ).pack(pady=18)

    def save(self):
        try:
            threshold = float(self.threshold_var.get())
            if threshold < 0:
                raise ValueError
        except Exception:
            messagebox.showerror("Erro", "Threshold deve ser um número real positivo.")
            return
        self.config["threshold"] = threshold
        save_config(self.config)
        messagebox.showinfo("Configurações", "Configurações salvas com sucesso!")
        self.window.destroy()
