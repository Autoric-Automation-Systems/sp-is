"""Página de criação/edição de receita."""
import logging
import tkinter as tk
from tkinter import messagebox

import cv2
from PIL import Image, ImageTk

from components import ui
from components.camera_view import orient_frame
from components.roi_selector import ROISelector
from services.config_service import load_config
from services.recipe_service import normalize_roi, save_recipe
from styles.theme import *
from views.base_page import Page

LOGGER = logging.getLogger(__name__)

FRAME_INTERVAL_MS = 30
MAX_NAME_LENGTH = 60
IMAGE_WIDTH = 640
IMAGE_HEIGHT = 480
DISPLAY_SCALE = 0.8
CANVAS_WIDTH = int(IMAGE_WIDTH * DISPLAY_SCALE)
CANVAS_HEIGHT = int(IMAGE_HEIGHT * DISPLAY_SCALE)


class RecipeEditPage(Page):
    route = "recipe_edit"

    def build(self):
        self.recipe = None
        self.current_frame = None
        self._photo = None
        self._image_item = None
        self._after_id = None
        self._last_roi_text = ""

        wrapper = ui.frame(self, "bg")
        wrapper.pack(fill="both", expand=True, padx=18, pady=10)
        wrapper.grid_columnconfigure(0, weight=1)
        wrapper.grid_rowconfigure(1, weight=1)

        header = ui.frame(wrapper, "bg")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ui.label(header, "RECEITA", kind="title").pack(side="left")
        self.mode_label = ui.label(header, "", kind="small")
        self.mode_label.pack(side="left", padx=(12, 0), pady=(6, 0))
        ui.button(
            header, "Voltar", command=self.cancel, variant="secondary", size="sm"
        ).pack(side="right")

        body = ui.frame(wrapper, "bg")
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(0, weight=1)

        # -------- câmera + ROI --------
        camera_panel = ui.panel(body, pack=False, padding=8)
        camera_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        canvas_frame = ui.frame(camera_panel.content, "card")
        canvas_frame.pack()
        self.canvas = ui.canvas(
            canvas_frame,
            width=CANVAS_WIDTH,
            height=CANVAS_HEIGHT,
            bg=CANVAS_BG,
            highlightthickness=1,
            highlightbackground=CANVAS_BORDER,
        )
        self.canvas.pack()

        hint = ui.frame(camera_panel.content, "card")
        hint.pack(fill="x", pady=(8, 0))
        self.roi_label = ui.label(hint, "", kind="small", bg=CARD, fg=PRIMARY)
        self.roi_label.pack(side="right")
        ui.paragraph(
            hint,
            "Arraste para desenhar o ROI · cantos amarelos redimensionam · "
            "arraste dentro para mover",
            kind="small",
            bg=CARD,
            padding=90,
        ).pack(side="left", fill="x", expand=True)

        # -------- formulário --------
        form_panel = ui.panel(body, pack=False, padding=16)
        form_panel.grid(row=0, column=1, sticky="nsew")
        form = form_panel.content

        ui.label(form, "NOME DA RECEITA", kind="small").pack(anchor="w")
        self.name = ui.entry(form, width=28, justify="left")
        self.name.pack(fill="x", pady=(4, 12), ipady=6)

        ui.label(form, "REGÃO DE INTERESSE (ROI)", kind="small").pack(anchor="w")
        roi_grid = ui.frame(form, "card")
        roi_grid.pack(fill="x", pady=(4, 12))
        self.roi_values = {}
        for index, (key, text) in enumerate(
            (("x1", "X1"), ("y1", "Y1"), ("x2", "X2"), ("y2", "Y2"))
        ):
            ui.label(roi_grid, text, kind="small", bg=CARD).grid(
                row=index // 2, column=(index % 2) * 2, sticky="w", pady=3
            )
            value = ui.label(roi_grid, "—", kind="body", bg=CARD)
            value.grid(
                row=index // 2, column=(index % 2) * 2 + 1,
                sticky="w", padx=(6, 20), pady=3,
            )
            self.roi_values[key] = value

        ui.separator(form, pady=8)

        self.summary = ui.label(form, "", kind="small", bg=CARD, justify="left")
        self.summary.pack(anchor="w", pady=(0, 12))

        actions = ui.frame(form, "card")
        actions.pack(fill="x", side="bottom")
        ui.button(
            actions, "Salvar receita", command=self.save, variant="success", size="lg"
        ).pack(fill="x", pady=(0, 6))
        ui.button(
            actions, "Cancelar", command=self.cancel, variant="secondary", size="md"
        ).pack(fill="x")

        self.roi_selector = ROISelector(
            self.canvas,
            scale=DISPLAY_SCALE,
            image_size=(IMAGE_WIDTH, IMAGE_HEIGHT),
        )

    # ------------------------------------------------------------------ navegação
    def set_recipe(self, recipe):
        self.recipe = recipe
        self.name.delete(0, "end")
        if recipe:
            self.name.insert(0, recipe["name"])
            self.roi_selector.set_original(recipe["roi"])
            self.mode_label.configure(text="Editando receita existente")
        else:
            self.roi_selector.original_roi = None
            self.roi_selector.roi = None
            self.roi_selector._delete_original_item()
            self.roi_selector._delete_editable_items()
            self.mode_label.configure(text="Nova receita")

        self.summary.configure(
            text=(
                "A imagem capturada agora será salva como referência da receita.\n"
                "Mantenha a peça na mesma posição usada na produção."
            )
        )
        self._update_roi_labels()

    def on_show(self):
        self.app.refresh_header_stats()
        self.name.focus_set()
        self.running = True
        if self._after_id is None:
            self.update_frame()

    def on_hide(self):
        self.running = False
        if self._after_id is not None:
            try:
                self.canvas.after_cancel(self._after_id)
            except tk.TclError:
                pass
            self._after_id = None

    # ------------------------------------------------------------------ vídeo
    def update_frame(self):
        if not self.running:
            return
        try:
            self._render_frame()
        except tk.TclError:
            self.running = False
            return
        except Exception:
            LOGGER.exception("Falha ao atualizar o vídeo")
        if self.running:
            try:
                self._after_id = self.canvas.after(FRAME_INTERVAL_MS, self.update_frame)
            except tk.TclError:
                self.running = False

    def _render_frame(self):
        frame = self.camera.get_frame()
        if frame is None:
            return

        frame = orient_frame(frame, load_config().get("rotate_180", True))
        self.current_frame = frame.copy()
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        image = Image.fromarray(frame_rgb).resize(
            (CANVAS_WIDTH, CANVAS_HEIGHT), Image.LANCZOS
        )
        if self._photo is None:
            self._photo = ImageTk.PhotoImage(image=image)
            self._image_item = self.canvas.create_image(0, 0, anchor="nw", image=self._photo)
        else:
            self._photo.paste(image)
        self.roi_selector.draw()
        self._update_roi_labels()

    def _update_roi_labels(self):
        roi = self.roi_selector.get_final_roi()
        if not roi:
            for value in self.roi_values.values():
                value.configure(text="—")
            self.roi_label.configure(text="sem ROI")
            return

        x1, x2 = sorted((roi["x1"], roi["x2"]))
        y1, y2 = sorted((roi["y1"], roi["y2"]))
        values = {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
        for key, value in values.items():
            self.roi_values[key].configure(text=str(value))

        width, height = x2 - x1, y2 - y1
        text = f"{width}×{height} px"
        if text != self._last_roi_text:
            self._last_roi_text = text
            self.roi_label.configure(text=text)

    # ------------------------------------------------------------------ ações
    def save(self):
        name = self.name.get().strip()
        if not name:
            messagebox.showerror("Erro", "Nome obrigatório", parent=self)
            return
        if len(name) > MAX_NAME_LENGTH:
            messagebox.showerror(
                "Erro", f"O nome deve ter no máximo {MAX_NAME_LENGTH} caracteres", parent=self
            )
            return

        roi = normalize_roi(self.roi_selector.get_final_roi())
        if roi is None:
            messagebox.showerror(
                "Erro", "Selecione um ROI válido (área diferente de zero)", parent=self
            )
            return

        if self.current_frame is None:
            messagebox.showerror(
                "Erro", "Nenhum quadro capturado da câmera", parent=self
            )
            return

        original_name = self.recipe["name"] if self.recipe else None
        success, error = save_recipe(name, roi, self.current_frame, original_name)
        if not success:
            messagebox.showerror("Erro", error, parent=self)
            return

        self.app.set_active_recipe_name(name)
        self.app.show_route("recipes")

    def cancel(self):
        self.app.show_route("recipes")
