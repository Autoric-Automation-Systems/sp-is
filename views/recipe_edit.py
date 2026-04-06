import tkinter as tk
from tkinter import messagebox
import cv2
from PIL import Image, ImageTk

from components.layout import BaseLayout
from components.camera_view import CameraView
from components.roi_selector import ROISelector
from services.recipe_service import save_recipe


class RecipeEditView:
    def __init__(self, parent, app, recipe):
        self.app = app
        self.recipe = recipe

        layout = BaseLayout(parent, app)
        self.frame = layout.frame

        tk.Label(layout.content, text="EDIÇÃO DE RECEITA", font=("Arial", 18)).pack(pady=10)

        # Nome
        self.name = tk.Entry(layout.content)
        self.name.pack(pady=5)

        if recipe:
            self.name.insert(0, recipe["name"])

        # Canvas câmera
        self.canvas = tk.Canvas(layout.content, width=640, height=480, bg="black")
        self.canvas.pack()

        # Camera
        self.camera = CameraView()

        # ROI
        self.roi_selector = ROISelector(self.canvas)

        if recipe:
            self.roi_selector.set_original(recipe["roi"])
        # Botões
        btns = tk.Frame(layout.content)
        btns.pack(pady=10)

        tk.Button(btns, text="Salvar", command=self.save).pack(side="left", padx=5)
        tk.Button(btns, text="Cancelar", command=self.cancel).pack(side="left", padx=5)

        # Loop
        self.running = True
        self.update_frame()

    # -------- CAMERA LOOP --------
    def update_frame(self):
        if not self.running:
            return

        frame = self.camera.get_frame()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        self.current_frame = frame.copy()

        img = Image.fromarray(frame)
        imgtk = ImageTk.PhotoImage(image=img)

        self.canvas.imgtk = imgtk
        self.canvas.create_image(0, 0, anchor="nw", image=imgtk)

        # desenha ROI
        self.roi_selector.draw()

        self.canvas.after(30, self.update_frame)

    # -------- SAVE --------
    def save(self):
        name = self.name.get().strip()

        if not name:
            messagebox.showerror("Erro", "Nome obrigatório")
            return

        roi = self.roi_selector.get_final_roi()
        if not roi:
            messagebox.showerror("Erro", "Selecione ROI")
            return

        original_name = self.recipe["name"] if self.recipe else None

        success, error = save_recipe(
            name,
            roi,
            self.current_frame,
            original_name
        )

        if not success:
            messagebox.showerror("Erro", error)
            return

        self.cleanup()
        self.app.show_recipes()

    # -------- CANCEL --------
    def cancel(self):
        self.cleanup()
        self.app.show_recipes()

    # -------- CLEANUP --------
    def cleanup(self):
        self.running = False
        self.camera.stop()