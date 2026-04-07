import tkinter as tk
import cv2
from PIL import Image, ImageTk

from components.layout import BaseLayout
from components.camera_view import CameraView
from styles.theme import *
from services.recipe_service import list_recipes
from services.vision_service import compare_roi

class ProductionView:
    def __init__(self, parent, app):
        self.app = app

        layout = BaseLayout(parent, app)
        layout.content.configure(bg=BG)

        # -------- RECEITAS --------
        self.recipes = list_recipes()
        self.recipe_names = [r["name"] for r in self.recipes]
        self.selected_recipe = tk.StringVar()
        if self.recipe_names:
            self.selected_recipe.set(self.recipe_names[0])
            self.set_recipe(self.recipe_names[0])

        # -------- MAIN GRID --------
        main = tk.Frame(layout.content, bg=BG)
        main.pack(fill="both", expand=True, padx=32, pady=32)
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=2)
        main.columnconfigure(2, weight=1)

        # -------- ESQUERDA (RECEITA) --------
        left = tk.Frame(main, bg=BG)
        left.grid(row=0, column=0, sticky="n", padx=20, pady=20)
        tk.Label(left, text="Receita", bg=BG, fg=TEXT, font=FONT_HEADER).pack(pady=5)
        tk.OptionMenu(
            left,
            self.selected_recipe,
            *self.recipe_names,
            command=self.set_recipe
        ).pack(pady=10, ipadx=10, ipady=4)

        # -------- CENTRO (CAMERA) --------
        center = tk.Frame(main, bg=BG)
        center.grid(row=0, column=1)
        self.canvas = tk.Canvas(
            center,
            width=640,
            height=480,
            bg=CANVAS_BG,
            highlightthickness=2,
            highlightbackground=CANVAS_BORDER
        )
        self.canvas.pack(pady=10)
        tk.Button(
            center,
            text="EXECUTAR CICLO",
            command=self.run_cycle,
            bg=PRIMARY,
            fg="white",
            font=BUTTON_FONT,
            relief="flat",
            width=25,
            height=2,
            activebackground=PRIMARY_ACTIVE,
            activeforeground="white",
            cursor="hand2"
        ).pack(pady=10)

        # -------- DIREITA (RESULTADO) --------
        right = tk.Frame(main, bg=BG)
        right.grid(row=0, column=2, sticky="n", padx=20, pady=20)
        tk.Label(right, text="Resultado", bg=BG, fg=TEXT, font=FONT_HEADER).pack(pady=5)
        self.status = tk.Label(
            right,
            text="---",
            bg=BG,
            fg=TEXT_DIM,
            font=("Segoe UI", 20, "bold")
        )
        self.status.pack(pady=10)
        self.time_label = tk.Label(
            right,
            text="- ms",
            bg=BG,
            fg=TEXT_DIM,
            font=FONT
        )
        self.time_label.pack()

        # -------- CAMERA --------
        self.camera = CameraView()

        # -------- LOOP --------
        self.running = True
        self.update_frame()

    def set_recipe(self, name):
        for r in self.recipes:
            if r["name"] == name:
                self.app.current_recipe = r
                break

    def update_frame(self):
        if not self.running:
            return
        frame = self.camera.get_frame()
        # Rotaciona 180 graus
        frame = cv2.rotate(frame, cv2.ROTATE_180)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if self.app.current_recipe:
            roi = self.app.current_recipe["roi"]
            x1, y1, x2, y2 = roi.values()
            cv2.rectangle(
                frame_rgb,
                (x1, y1),
                (x2, y2),
                (16, 185, 129),
                2
            )
        img = Image.fromarray(frame_rgb)
        imgtk = ImageTk.PhotoImage(image=img)
        self.canvas.imgtk = imgtk
        self.canvas.create_image(0, 0, anchor="nw", image=imgtk)
        self.canvas.after(30, self.update_frame)

    def run_cycle(self):
        import time
        from services.config_service import load_config
        config = load_config()
        threshold = config.get("threshold", 30)
        if not self.app.current_recipe:
            self.set_status("SEM RECEITA", DANGER)
            return
        start = time.time()
        frame = self.camera.get_frame()
        recipe = self.app.current_recipe
        roi = recipe["roi"]
        ref_img = cv2.imread(recipe["image"])
        score = compare_roi(frame, ref_img, roi)
        elapsed = int((time.time() - start) * 1000)
        if score < threshold:
            self.set_status("OK", SUCCESS, score, threshold)
        else:
            self.set_status("ERRO", DANGER, score, threshold)
        self.time_label.config(text=f"{elapsed} ms")

    def set_status(self, text, color, score=None, threshold=None):
        self.status.config(text=text, fg=color,)
        if score is not None:
            self.status.config(text=f"{text} (Score: {score})")
            self.status.config(text=f"{text} (Score: {score:.2f}, Threshold: {threshold})")

    def cleanup(self):
        self.running = False
        # self.camera.stop()