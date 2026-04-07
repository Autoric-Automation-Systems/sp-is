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
        card = Card(layout.content, width=800)

        # TÍTULO
        tk.Label(
            card.content,
            text="EDIÇÃO DE RECEITA",
            font=FONT_TITLE,
            bg=CARD,
            fg=TEXT
        ).pack(pady=(0, 18))

        # INPUT
        entry_frame = tk.Frame(card.content, bg=CARD)
        entry_frame.pack(pady=(0, 18), fill="x", padx=30)
        tk.Label(
            entry_frame,
            text="Nome da Receita:",
            font=FONT,
            bg=CARD,
            fg=TEXT_DIM,
            anchor="w"
        ).pack(side="left", padx=(0, 10))
        self.name = tk.Entry(
            entry_frame,
            bg=INPUT_BG,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            font=FONT,
            justify="center",
            highlightthickness=2,
            highlightbackground=INPUT_BORDER,
            highlightcolor=INPUT_FOCUS
        )
        self.name.pack(side="left", ipady=8, ipadx=10, fill="x", expand=True)
        if recipe:
            self.name.insert(0, recipe["name"])

        # CANVAS
        canvas_frame = tk.Frame(card.content, bg=CARD)
        canvas_frame.pack(pady=(0, 10))
        self.canvas = tk.Canvas(
            canvas_frame,
            width=640,
            height=480,
            bg=CANVAS_BG,
            highlightthickness=2,
            highlightbackground=CANVAS_BORDER
        )
        self.canvas.pack()

        # CAMERA
        self.camera = CameraView()

        # ROI
        self.roi_selector = ROISelector(self.canvas)
        if recipe:
            self.roi_selector.set_original(recipe["roi"])

        # BOTÕES
        btns = tk.Frame(card.content, bg=CARD)
        btns.pack(pady=18)
        save_btn = tk.Button(
            btns,
            text="Salvar",
            command=self.save,
            bg=SUCCESS,
            fg=TEXT,
            font=BUTTON_FONT,
            activebackground=SUCCESS,
            activeforeground=TEXT,
            relief="flat",
            width=16,
            bd=0,
            highlightthickness=0,
            cursor="hand2"
        )
        save_btn.pack(side="left", padx=12, ipadx=4, ipady=4)
        cancel_btn = tk.Button(
            btns,
            text="Cancelar",
            command=self.cancel,
            bg=BUTTON_BG,
            fg=TEXT,
            font=BUTTON_FONT,
            activebackground=BUTTON_ACTIVE,
            activeforeground=TEXT,
            relief="flat",
            width=16,
            bd=0,
            highlightthickness=0,
            cursor="hand2"
        )
        cancel_btn.pack(side="left", padx=12, ipadx=4, ipady=4)

        self.running = True
        self.update_frame()

    def update_frame(self):
        if not self.running:
            return
        frame = self.camera.get_frame()
        frame = cv2.rotate(frame, cv2.ROTATE_180)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.current_frame = frame_rgb.copy()
        img = Image.fromarray(frame_rgb)
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
        # Validação de ROI
        x1, y1, x2, y2 = roi["x1"], roi["y1"], roi["x2"], roi["y2"]
        if x1 == x2 or y1 == y2:
            messagebox.showerror("Erro", "Selecione um ROI válido (área diferente de zero)")
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
        # self.camera.stop()