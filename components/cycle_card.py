import tkinter as tk
import time

from styles.theme import *
from services.vision_service import compare_roi


class CycleCard:
    def __init__(self, parent, app, camera):
        self.app = app
        self.camera = camera

        # -------- FRAME --------
        self.frame = tk.Frame(
            parent,
            bg=CARD,
            highlightthickness=1,
            highlightbackground=BORDER,
            width=300,
            height=220
        )
        self.frame.pack_propagate(False)
        self.frame.pack(side="left", padx=20, pady=20)

        # -------- TÍTULO --------
        tk.Label(
            self.frame,
            text="CICLO",
            bg=CARD,
            fg=TEXT_DIM,
            font=FONT_TITLE
        ).pack(pady=(10, 5))

        # -------- STATUS --------
        self.status = tk.Label(
            self.frame,
            text="AGUARDANDO",
            bg=CARD,
            fg=TEXT_DIM,
            font=("Segoe UI", 18, "bold")
        )
        self.status.pack(pady=5)

        # -------- TEMPO --------
        self.time_label = tk.Label(
            self.frame,
            text="- ms",
            bg=CARD,
            fg=TEXT_DIM,
            font=FONT
        )
        self.time_label.pack(pady=5)

        # -------- BOTÃO --------
        tk.Button(
            self.frame,
            text="EXECUTAR CICLO",
            command=self.run_cycle,
            bg=PRIMARY,
            fg="white",
            relief="flat",
            height=2
        ).pack(fill="x", padx=20, pady=15)

    # -------- CICLO --------
    def run_cycle(self):
        if not self.app.current_recipe:
            self.set_status("SEM RECEITA", DANGER)
            return

        start = time.time()

        # captura frame
        frame = self.camera.get_frame()

        recipe = self.app.current_recipe

        # carrega imagem referência
        ref_img = recipe["image"]
        roi = recipe["roi"]

        score = compare_roi(frame, ref_img, roi)

        elapsed = int((time.time() - start) * 1000)

        # decisão simples
        if score < 10:
            self.set_status("OK", SUCCESS)
        else:
            self.set_status("ERRO", DANGER)

        self.time_label.config(text=f"{elapsed} ms")

    # -------- STATUS --------
    def set_status(self, text, color):
        self.status.config(text=text, fg=color)