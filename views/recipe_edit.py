import tkinter as tk
from tkinter import messagebox
import cv2
from PIL import Image, ImageTk

from components.layout import BaseLayout
from components.card import Card
from components.camera_view import CameraView
from components.roi_selector import ROISelector
from services.recipe_service import save_recipe

from styles.theme import *

class RecipeEditView:
    def __init__(self, parent, app, recipe):
        self.app = app
        self.recipe = recipe

        layout = BaseLayout(parent, app)

        card = Card(layout.content)

        # TÍTULO
        tk.Label(
            card.content,
            text="EDIÇÃO DE RECEITA",
            font=FONT_TITLE,
            bg=CARD,
            fg=TEXT
        ).pack(pady=(0, 18))

        # INPUT
        self.name = tk.Entry(
            card.content,
            bg=INPUT_BG,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            font=FONT,
            justify="center",
            highlightthickness=1,
            highlightbackground=INPUT_BORDER,
            highlightcolor=INPUT_FOCUS
        )
        self.name.pack(pady=(0, 18), ipady=8, ipadx=10, fill="x", padx=30)

        if recipe:
            self.name.insert(0, recipe["name"])

        # CANVAS
        self.canvas = tk.Canvas(
                card.content,
                width=640,
                height=400,  # Reduza a altura para caber tudo
                bg=CANVAS_BG,
                highlightthickness=2,
                highlightbackground=CANVAS_BORDER
            )
        self.canvas.pack(pady=(0, 10))

        # CAMERA
        self.camera = CameraView()

        # ROI
        self.roi_selector = ROISelector(self.canvas)

        if recipe:
            self.roi_selector.set_original(recipe["roi"])

        # BOTÕES
        btns = tk.Frame(card.content, bg=BG)  # Use BG para contraste
        btns.pack(pady=18)

        tk.Button(
            btns,
            text="Salvar",
            command=self.save,
            bg=SUCCESS,
            fg=TEXT,
            font=BUTTON_FONT,
            activebackground=SUCCESS,
            activeforeground=TEXT,
            relief="flat",
            width=14,
            bd=0,
            highlightthickness=0,
            cursor="hand2"
        ).pack(side="left", padx=8)

        tk.Button(
            btns,
            text="Cancelar",
            command=self.cancel,
            bg=BUTTON_BG,
            fg=TEXT,
            font=BUTTON_FONT,
            activebackground=BUTTON_ACTIVE,
            activeforeground=TEXT,
            relief="flat",
            width=14,
            bd=0,
            highlightthickness=0,
            cursor="hand2"
        ).pack(side="left", padx=8)

        self.running = True
        self.update_frame()

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

        self.roi_selector.draw()

        self.canvas.after(30, self.update_frame)

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

    def cancel(self):
        self.cleanup()
        self.app.show_recipes()

    def cleanup(self):
        self.running = False
        self.camera.stop()