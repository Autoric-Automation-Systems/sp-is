import tkinter as tk
from components.layout import BaseLayout
from services.recipe_service import save_recipe
from picamera2 import Picamera2
import cv2
from PIL import Image, ImageTk
import os
from tkinter import messagebox


class RecipeEditView:
    def __init__(self, parent, app, recipe):
        self.app = app
        self.recipe = recipe

        layout = BaseLayout(parent, app)

        tk.Label(layout.content, text="EDIÇÃO DE RECEITA", font=("Arial", 18)).pack(pady=10)

        # Nome
        self.name = tk.Entry(layout.content)
        self.name.pack()
        if recipe:
            self.name.insert(0, recipe["name"])

        # Canvas câmera
        self.canvas = tk.Canvas(layout.content, width=640, height=480, bg="black")
        self.canvas.pack()

        # ROI
        self.start_x = None
        self.start_y = None
        self.rect = None
        self.roi = None

        self.canvas.bind("<ButtonPress-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        # Botões
        btns = tk.Frame(layout.content)
        btns.pack(pady=10)
        tk.Button(btns, text="Salvar", command=self.save).pack(side="left", padx=5)
        tk.Button(btns, text="Cancelar", command=self.cancel).pack(side="left", padx=5)

        # Camera
        self.picam2 = Picamera2()
        self.picam2.start()

        self.update_frame()

    # -------- CAMERA LOOP --------
    def update_frame(self):
        frame = self.picam2.capture_array()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        self.current_frame = frame.copy()

        img = Image.fromarray(frame)
        imgtk = ImageTk.PhotoImage(image=img)

        self.canvas.imgtk = imgtk
        self.canvas.create_image(0, 0, anchor="nw", image=imgtk)

        self.canvas.after(30, self.update_frame)

    # -------- ROI EVENTS --------
    def on_click(self, event):
        self.start_x = event.x
        self.start_y = event.y

        if self.rect:
            self.canvas.delete(self.rect)

    def on_drag(self, event):
        if self.rect:
            self.canvas.delete(self.rect)

        self.rect = self.canvas.create_rectangle(
            self.start_x,
            self.start_y,
            event.x,
            event.y,
            outline="red",
            width=2
        )

    def on_release(self, event):
        self.roi = {
            "x1": self.start_x,
            "y1": self.start_y,
            "x2": event.x,
            "y2": event.y
        }

        print("ROI:", self.roi)

    def save(self):
        name = self.name.get().strip()

        if not name:
            messagebox.showerror("Erro", "Nome obrigatório")
            return

        if not self.roi:
            messagebox.showerror("Erro", "Selecione ROI")
            return

        success, error = save_recipe(name, self.roi, self.current_frame)

        if not success:
            messagebox.showerror("Erro", error)
            return

        self.picam2.stop()
        self.app.show_recipes()

    def cancel(self):
        try:
            self.picam2.stop()
        except:
            pass

        self.app.show_recipes()