"""Página de criação/edição de receita: dois ROIs nomeáveis e sua janela de acerto."""
import logging
import tkinter as tk
from tkinter import messagebox

import cv2
from PIL import Image, ImageTk

from components import ui
from components.camera_view import orient_frame
from components.roi_selector import ROISelector
from services.config_service import load_config
from services.recipe_service import (
    ROI_COLORS,
    ROI_COUNT,
    default_roi_entry,
    load_reference_image,
    normalize_roi_entry,
    save_recipe,
)
from services.vision_service import (
    DEFAULT_MAX_MATCH,
    DEFAULT_MIN_MATCH,
    evaluate_rois,
    parse_percent,
)
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

COORD_STEP = 5
MATCH_STEP = 1.0
# O % de acerto é recalculado a cada N frames: rápido para ajustar, leve para a CPU.
MATCH_EVERY_FRAMES = 8

COORD_LIMITS = (0, IMAGE_WIDTH, 0, IMAGE_HEIGHT)


class RecipeEditPage(Page):
    route = "recipe_edit"

    def build(self):
        self.recipe = None
        self.current_frame = None
        self.reference = None
        self._photo = None
        self._image_item = None
        self._after_id = None
        self._frame_count = 0
        self._syncing = False
        self.roi_vars = []
        self.roi_live = []
        self.roi_state = []
        self.roi_titles = []

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
        body.grid_columnconfigure(1, weight=0, minsize=440)
        body.grid_rowconfigure(0, weight=1)

        self._build_canvas(body)
        self._build_form(body)

        self.roi_selector = ROISelector(
            self.canvas,
            scale=DISPLAY_SCALE,
            image_size=(IMAGE_WIDTH, IMAGE_HEIGHT),
            on_change=self._on_selector_change,
        )

    # ------------------------------------------------------------------ canvas
    def _build_canvas(self, body):
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
            "Arraste para desenhar o ROI ativo · cantos redimensionam · "
            "clique dentro de outro ROI para selecioná-lo",
            kind="small",
            bg=CARD,
            padding=90,
        ).pack(side="left", fill="x", expand=True)

        reference_row = ui.frame(camera_panel.content, "card")
        reference_row.pack(fill="x", pady=(6, 0))
        self.reference_label = ui.label(
            reference_row, "", kind="small", bg=CARD
        )
        self.reference_label.pack(side="left", fill="x", expand=True)
        ui.button(
            reference_row,
            "Capturar referência",
            command=self.capture_reference,
            size="sm",
        ).pack(side="right")

    # ------------------------------------------------------------------ formulário
    def _build_form(self, body):
        form_panel = ui.panel(body, pack=False, padding=12)
        form_panel.grid(row=0, column=1, sticky="nsew")

        actions = ui.frame(form_panel.content, "card")
        actions.pack(fill="x", side="bottom", pady=(8, 0))
        ui.button(
            actions, "Salvar receita", command=self.save, variant="success", size="lg"
        ).pack(fill="x", pady=(0, 6))
        ui.button(
            actions, "Cancelar", command=self.cancel, variant="secondary", size="md"
        ).pack(fill="x")

        container, form = ui.scrollable(form_panel.content, bg=CARD)
        container.pack(fill="both", expand=True)

        ui.label(form, "NOME DA RECEITA", kind="small", bg=CARD).pack(anchor="w")
        self.name = ui.entry(form, width=28, justify="left")
        self.name.pack(fill="x", pady=(4, 10), ipady=6)

        for index in range(ROI_COUNT):
            self._build_roi_card(form, index)

        ui.label(
            form,
            "O % de acerto compara cada ROI com a imagem de referência da receita. "
            "A peça é aprovada quando todos os ROIs ficam dentro da janela.",
            kind="small",
            bg=CARD,
            justify="left",
            wraplength=380,
        ).pack(anchor="w", pady=(4, 10))

    def _build_roi_card(self, parent, index):
        color = ROI_COLORS[index % len(ROI_COLORS)]
        card = ui.panel(parent, pack=False, padding=8)
        card.pack(fill="x", pady=(0, 8))
        content = card.content

        variables = {
            "name": tk.StringVar(),
            "x1": tk.StringVar(),
            "y1": tk.StringVar(),
            "x2": tk.StringVar(),
            "y2": tk.StringVar(),
            "min": tk.StringVar(),
            "max": tk.StringVar(),
        }
        self.roi_vars.append(variables)

        # Título e nome na mesma linha: o card precisa caber sem rolagem.
        title_row = ui.frame(content, "card")
        title_row.pack(fill="x", pady=(0, 4))
        ui.label(title_row, "■", kind="bold", bg=CARD, fg=color).pack(side="left")
        title = ui.label(title_row, f"ROI {index + 1}", kind="bold", bg=CARD)
        title.pack(side="left", padx=(6, 8))
        self.roi_titles.append(title)
        ui.entry(title_row, variables["name"], width=10, justify="left").pack(
            side="left", fill="x", expand=True
        )

        grid = ui.frame(content, "card")
        grid.pack(fill="x")
        for row, keys in enumerate((("x1", "y1"), ("x2", "y2"))):
            for column, key in enumerate(keys):
                self._number_field(
                    grid,
                    row,
                    column,
                    key.upper(),
                    variables[key],
                    COORD_STEP,
                    (COORD_LIMITS[1] if key.startswith("x") else COORD_LIMITS[3]),
                )
        grid.grid_columnconfigure(1, weight=1)
        grid.grid_columnconfigure(3, weight=1)

        window_row = ui.frame(content, "card")
        window_row.pack(fill="x", pady=(4, 0))
        ui.label(window_row, "Acerto", kind="small", bg=CARD).grid(
            row=0, column=0, sticky="w", pady=2, padx=(0, 10)
        )
        self._number_field(
            window_row, 0, 1, "mín", variables["min"], MATCH_STEP, 100, compact=True
        )
        self._number_field(
            window_row, 0, 2, "máx", variables["max"], MATCH_STEP, 100, compact=True
        )

        live_row = ui.frame(content, "card")
        live_row.pack(fill="x", pady=(2, 0))
        ui.label(live_row, "Agora:", kind="small", bg=CARD).pack(side="left")
        live = ui.label(live_row, "—", kind="bold", bg=CARD, fg=TEXT_DIM)
        live.pack(side="left", padx=(6, 8))
        state = ui.label(live_row, "", kind="small", bg=CARD, fg=TEXT_DIM)
        state.pack(side="left")
        self.roi_live.append(live)
        self.roi_state.append(state)

        for key, variable in variables.items():
            variable.trace_add("write", lambda *_args, i=index: self._on_fields_changed(i))

    def _number_field(self, parent, row, column, text, variable, step, maximum,
                      compact=False):
        ui.label(parent, text, kind="small", bg=CARD).grid(
            row=row, column=column * 2, sticky="w", pady=2, padx=(0, 2)
        )
        box = ui.frame(parent, "card")
        box.grid(
            row=row,
            column=column * 2 + 1,
            sticky="w",
            padx=(0, 6 if compact else 10),
            pady=2,
        )
        ui.button(
            box,
            "−",
            command=lambda: self._bump(variable, -step, maximum),
            size="sm",
            width=26,
        ).pack(side="left")
        ui.entry(
            box,
            variable,
            width=4,
            px_width=64 if compact else 78,
            justify="center",
        ).pack(side="left", padx=2)
        ui.button(
            box,
            "+",
            command=lambda: self._bump(variable, step, maximum),
            size="sm",
            width=26,
        ).pack(side="left")

    @staticmethod
    def _bump(variable, delta, maximum):
        """Botão − / + dos campos: permite ajuste fino em tela touch."""
        try:
            value = float(variable.get().replace(",", "."))
        except (TypeError, ValueError):
            return
        value = min(maximum, max(0.0, value + delta))
        text = f"{value:g}"
        variable.set(text)

    # ------------------------------------------------------------------ dados
    def set_recipe(self, recipe):
        self.recipe = recipe
        self._syncing = True
        try:
            self.name.delete(0, "end")
            if recipe:
                self.name.insert(0, recipe["name"])
                entries = recipe.get("rois") or []
                self.reference = load_reference_image(recipe)
                self.mode_label.configure(text="Editando receita existente")
            else:
                entries = [default_roi_entry(i) for i in range(ROI_COUNT)]
                self.reference = None
                self.mode_label.configure(text="Nova receita")

            for index in range(ROI_COUNT):
                entry = entries[index] if index < len(entries) else default_roi_entry(index)
                self._write_fields(index, entry)
        finally:
            self._syncing = False

        self._sync_selector()
        self._update_reference_label()
        self._refresh_live()

    def _write_fields(self, index, entry):
        variables = self.roi_vars[index]
        box = entry.get("roi") or {}
        variables["name"].set(entry.get("name") or f"ROI {index + 1}")
        for key in ("x1", "y1", "x2", "y2"):
            variables[key].set(str(int(box.get(key, 0))))
        variables["min"].set(f"{float(entry.get('min_match', DEFAULT_MIN_MATCH)):g}")
        variables["max"].set(f"{float(entry.get('max_match', DEFAULT_MAX_MATCH)):g}")

    def _parse_rect(self, index):
        variables = self.roi_vars[index]
        values = {}
        for key in ("x1", "y1", "x2", "y2"):
            try:
                values[key] = int(round(float(variables[key].get().replace(",", "."))))
            except (TypeError, ValueError):
                return None
        values["x1"] = max(0, min(values["x1"], IMAGE_WIDTH))
        values["x2"] = max(0, min(values["x2"], IMAGE_WIDTH))
        values["y1"] = max(0, min(values["y1"], IMAGE_HEIGHT))
        values["y2"] = max(0, min(values["y2"], IMAGE_HEIGHT))
        if values["x1"] == values["x2"] or values["y1"] == values["y2"]:
            return None
        return values

    def _entry_from_fields(self, index):
        variables = self.roi_vars[index]
        rect = self._parse_rect(index) or {"x1": 0, "y1": 0, "x2": 0, "y2": 0}
        return {
            "name": variables["name"].get(),
            "roi": rect,
            "min_match": variables["min"].get(),
            "max_match": variables["max"].get(),
        }

    def _current_specs(self):
        """ROIs no formato do avaliador, preservando a ordem (índice = ROI)."""
        specs = []
        for index in range(ROI_COUNT):
            entry = normalize_roi_entry(self._entry_from_fields(index), index)
            if entry is None:
                # Mantém a posição para o % ao vivo casar com o card correto.
                entry = {
                    "name": self._roi_names()[index] or f"ROI {index + 1}",
                    "roi": None,
                    "min_match": DEFAULT_MIN_MATCH,
                    "max_match": DEFAULT_MAX_MATCH,
                }
            specs.append(entry)
        return specs

    def _roi_names(self):
        return [self.roi_vars[i]["name"].get().strip() for i in range(ROI_COUNT)]

    # ------------------------------------------------------------------ sincronização
    def _on_fields_changed(self, index):
        if self._syncing:
            return
        name = self.roi_vars[index]["name"].get().strip()
        self.roi_titles[index].configure(text=f"ROI {index + 1}")
        self._sync_selector()
        self.roi_label.configure(
            text=f"{len([n for n in self._roi_names() if n])} ROI(s) · "
            f"editando {name or f'ROI {index + 1}'}"
        )

    def _sync_selector(self):
        self._syncing = True
        try:
            rects = [self._parse_rect(index) for index in range(ROI_COUNT)]
            self.roi_selector.set_regions(rects, labels=self._roi_names())
        finally:
            self._syncing = False
        self._update_roi_label()

    def _on_selector_change(self, index):
        if self._syncing:
            return
        rect = self.roi_selector.get_region(index)
        if rect is None:
            return
        self._syncing = True
        try:
            for key in ("x1", "y1", "x2", "y2"):
                self.roi_vars[index][key].set(str(int(rect[key])))
        finally:
            self._syncing = False
        self._update_roi_label()

    def _update_roi_label(self):
        rect = self.roi_selector.get_region(self.roi_selector.active)
        name = (self._roi_names()[self.roi_selector.active] or
                f"ROI {self.roi_selector.active + 1}")
        if rect is None:
            self.roi_label.configure(text=f"{name}: sem área")
            return
        width = abs(rect["x2"] - rect["x1"])
        height = abs(rect["y2"] - rect["y1"])
        self.roi_label.configure(text=f"{name} · {width}×{height} px")

    def _update_reference_label(self):
        if self.reference is None:
            text = "Sem referência: capture ou salve para usar o frame atual."
            color = WARNING
        else:
            text = "Referência carregada (imagem usada no % de acerto)."
            color = TEXT_DIM
        self.reference_label.configure(text=text, text_color=color)

    def capture_reference(self):
        """Usa o frame atual como referência para calibrar a janela de acerto."""
        if self.current_frame is None:
            messagebox.showerror("Referência", "Nenhum quadro capturado da câmera.", parent=self)
            return
        self.reference = self.current_frame.copy()
        self._update_reference_label()
        self._refresh_live()

    # ------------------------------------------------------------------ vídeo
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

        self._frame_count += 1
        if self._frame_count % MATCH_EVERY_FRAMES == 0:
            self._refresh_live()

    # ------------------------------------------------------------------ %
    def _refresh_live(self):
        """Mostra o % de acerto atual de cada ROI (ajuda a calibrar a janela)."""
        if self.reference is None or self.current_frame is None:
            reason = "sem referência" if self.reference is None else "aguardando vídeo"
            for label, state in zip(self.roi_live, self.roi_state):
                label.configure(text="—", text_color=TEXT_DIM)
                state.configure(text=reason, text_color=TEXT_DIM)
            return

        evaluation = evaluate_rois(
            self.current_frame, self.reference, self._current_specs()
        )
        entries = evaluation.get("rois") or []

        for index in range(ROI_COUNT):
            entry = entries[index] if index < len(entries) else None
            if entry is None:
                self.roi_live[index].configure(text="—", text_color=TEXT_DIM)
                self.roi_state[index].configure(text="ROI inválido", text_color=WARNING)
                continue

            match = entry.get("match")
            if match is None:
                self.roi_live[index].configure(text="—", text_color=TEXT_DIM)
                self.roi_state[index].configure(text="ROI inválido", text_color=WARNING)
                continue

            self.roi_live[index].configure(
                text=f"{match:.1f}%",
                text_color=SUCCESS if entry["ok"] else DANGER,
            )
            if entry["ok"]:
                detail = f"OK · janela {entry['min']:g}–{entry['max']:g}%"
            elif match < entry["min"]:
                detail = f"abaixo de {entry['min']:g}%"
            else:
                detail = f"acima de {entry['max']:g}%"
            self.roi_state[index].configure(
                text=detail,
                text_color=SUCCESS if entry["ok"] else DANGER,
            )

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

        if self.current_frame is None and self.reference is None:
            messagebox.showerror(
                "Erro", "Nenhum quadro capturado da câmera", parent=self
            )
            return

        rois = []
        for index in range(ROI_COUNT):
            variables = self.roi_vars[index]
            low = parse_percent(variables["min"].get())
            high = parse_percent(variables["max"].get())
            if low is None or high is None:
                messagebox.showerror(
                    "Erro",
                    f"ROI {index + 1}: janela de acerto inválida. "
                    "Use números entre 0 e 100 (ex.: 85 e 100).",
                    parent=self,
                )
                return
            if low > high:
                messagebox.showerror(
                    "Erro",
                    f"ROI {index + 1}: o mínimo da janela deve ser menor que o máximo.",
                    parent=self,
                )
                return

            entry = normalize_roi_entry(
                self._entry_from_fields(index), index, (IMAGE_HEIGHT, IMAGE_WIDTH)
            )
            if entry is None:
                messagebox.showerror(
                    "Erro",
                    f"ROI {index + 1}: selecione uma área válida (diferente de zero)",
                    parent=self,
                )
                return
            rois.append(entry)

        if len({entry["name"].lower() for entry in rois}) != len(rois):
            messagebox.showerror("Erro", "Cada ROI deve ter um nome diferente", parent=self)
            return

        # Salva como referência a imagem em que a janela foi calibrada.
        frame = self.reference if self.reference is not None else self.current_frame
        original_name = self.recipe["name"] if self.recipe else None
        success, error = save_recipe(name, rois, frame, original_name)
        if not success:
            messagebox.showerror("Erro", error, parent=self)
            return

        self.app.set_active_recipe_name(name)
        self.app.show_route("recipes")

    def cancel(self):
        self.app.show_route("recipes")
