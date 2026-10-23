"""Página Principal: vídeo ao vivo, última captura analisada, miniaturas e trigger.

Regras de comportamento:
- o canvas grande mostra SEMPRE o vídeo ao vivo (nunca congela numa captura);
- a captura analisada aparece no painel "Última captura", com métricas;
- clicar numa miniatura carrega aquela análise no painel (o vídeo segue ao vivo);
- "Ampliar" abre a captura analisada em tamanho grande.
"""
import logging
import tkinter as tk

import customtkinter as ctk
import cv2
from PIL import Image, ImageOps, ImageTk

from components import ui
from components.camera_view import orient_frame
from services.config_service import load_config
from services.io_service import get_io
from services.recipe_service import list_recipes
from services.run_cycle import RunCycle
from services.trigger_service import TriggerService
from services.vision_service import clamp_roi
from styles.theme import *
from views.analysis import AnalysisDialog, record_image
from views.base_page import Page
from views.stats import StatsDialog

LOGGER = logging.getLogger(__name__)

CANVAS_WIDTH = 760
CANVAS_HEIGHT = 400
THUMB_WIDTH = 84
THUMB_HEIGHT = 44
THUMB_COUNT = 10
FRAME_INTERVAL_MS = 40

PREVIEW_WIDTH = 264
PREVIEW_HEIGHT = 104


class MainPage(Page):
    route = "main"

    def build(self):
        self.io = get_io()
        self.config = load_config()
        self.cycle_service = RunCycle(self)
        self._after_id = None
        self._photo = None
        self._canvas_item = None
        self._preview_photo = None
        self._thumb_photos = []
        self._trigger = None
        self._selected_record = None
        self._last_record = None

        self.recipes = list_recipes()
        self.recipe_names = [recipe["name"] for recipe in self.recipes]
        self.selected_recipe = tk.StringVar(
            value=(self.app.current_recipe or {}).get("name", "")
        )

        wrapper = ui.frame(self, "bg")
        wrapper.pack(fill="both", expand=True, padx=18, pady=10)
        wrapper.grid_columnconfigure(0, weight=1)
        wrapper.grid_rowconfigure(1, weight=1)

        self._build_top(wrapper)
        self._build_body(wrapper)

    # ------------------------------------------------------------------ topo
    def _build_top(self, parent):
        top = ui.frame(parent, "bg")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        top.grid_columnconfigure(2, weight=1)

        recipe_panel = ui.panel(top, pack=False, padding=10)
        recipe_panel.grid(row=0, column=0, sticky="w")
        ui.label(recipe_panel.content, "RECEITA EM USO", kind="small").pack(anchor="w")
        row = ui.frame(recipe_panel.content, "card")
        row.pack(fill="x", pady=(4, 0))
        self.recipe_combo = ui.dropdown(row, self.selected_recipe, self.recipe_names, width=18)
        self.recipe_combo.pack(side="left")
        ui.button(row, "Usar", command=self._use_selected_recipe, size="sm").pack(
            side="left", padx=(8, 0)
        )

        info_panel = ui.panel(top, pack=False, padding=10)
        info_panel.grid(row=0, column=1, sticky="w", padx=(10, 0))
        ui.label(info_panel.content, "TRIGGER", kind="small").pack(anchor="w")
        trigger_pin = self.config["trigger"]["pin"]
        ui.label(
            info_panel.content, f"Botão da tela + PIN {trigger_pin}", kind="bold"
        ).pack(anchor="w", pady=(1, 0))
        self.camera_label = ui.label(
            info_panel.content, f"Câmera: {self.camera.backend_name}", kind="small"
        )
        self.camera_label.pack(anchor="w")

        live_panel = ui.panel(top, pack=False, padding=10)
        live_panel.grid(row=0, column=2, sticky="e")
        ui.label(live_panel.content, "VÍDEO", kind="small").pack(anchor="e")
        self.live_label = ui.label(
            live_panel.content, "AO VIVO", kind="bold", fg=SUCCESS
        )
        self.live_label.pack(anchor="e", pady=(1, 0))

    # ------------------------------------------------------------------ corpo
    def _build_body(self, parent):
        body = ui.frame(parent, "bg")
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(0, weight=1)

        left = ui.frame(body, "bg")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left.grid_rowconfigure(0, weight=1)
        left.grid_columnconfigure(0, weight=1)

        image_panel = ui.panel(left, pack=False, padding=8)
        image_panel.grid(row=0, column=0, sticky="nsew")
        self.canvas = ui.canvas(
            image_panel.content,
            width=CANVAS_WIDTH,
            height=CANVAS_HEIGHT,
            bg=CANVAS_BG,
        )
        self.canvas.pack(fill="both", expand=True)

        self._build_thumbnails(left)

        side = ui.panel(body, pack=False, padding=14)
        side.grid(row=0, column=1, sticky="nsew")

        ui.label(side.content, "ÚLTIMA CAPTURA ANALISADA", kind="small").pack(anchor="w")

        self.detail_result = ui.label(side.content, "Aguardando", kind="value")
        self.detail_result.pack(anchor="w", pady=(0, 4))

        # Reserva o rodapé antes do conteúdo para os botões nunca serem cortados.
        buttons = ui.frame(side.content, "card")
        buttons.pack(fill="x", side="bottom")
        ui.button(
            buttons, "EXECUTAR CICLO", command=self.run_cycle, variant="primary", size="lg"
        ).pack(fill="x", pady=(0, 6))

        small = ui.frame(buttons, "card")
        small.pack(fill="x")
        self.open_button = ui.button(
            small,
            "Ampliar imagem",
            command=self._open_analysis,
            size="sm",
            state="disabled",
        )
        self.open_button.pack(side="left", fill="x", expand=True, padx=(0, 3))
        ui.button(
            small,
            "Estatísticas",
            command=lambda: StatsDialog(self.app, self.app),
            size="sm",
        ).pack(side="left", fill="x", expand=True, padx=(3, 0))

        # O CTkLabel não lida bem com image=None depois de ter imagem; o preview
        # é recriado a cada atualização dentro deste contêiner.
        self.preview_holder = ctk.CTkFrame(
            side.content,
            fg_color=INPUT_BG,
            corner_radius=6,
            width=PREVIEW_WIDTH,
            height=PREVIEW_HEIGHT,
        )
        self.preview_holder.pack(pady=(0, 6))
        self.preview_holder.pack_propagate(False)
        self.preview_holder.bind("<Button-1>", lambda _event: self._open_analysis())
        self._preview_photo = None
        self._set_preview(None)

        info = ui.frame(side.content, "card")
        info.pack(fill="x")
        self.detail_values = {}
        fields = (
            ("Receita", 0, 0), ("Horário", 0, 2),
            ("Score", 1, 0), ("Limiar", 1, 2),
            ("Brilho", 2, 0), ("Tempo", 2, 2),
        )
        for key, row_index, column in fields:
            ui.label(info, key, kind="small", fg=TEXT_DIM).grid(
                row=row_index, column=column, sticky="w", pady=0
            )
            value = ui.label(info, "—", kind="body")
            value.grid(
                row=row_index, column=column + 1, sticky="e", pady=0,
                padx=(4, 12 if column == 0 else 0),
            )
            self.detail_values[key] = value
        info.grid_columnconfigure(1, weight=1)
        info.grid_columnconfigure(3, weight=1)

        # RunCycle atualiza estes dois widgets.
        self.status = self.detail_result
        self.time_label = ctk.CTkLabel(side.content, text="", fg_color=CARD, height=1)

    # ------------------------------------------------------------------ miniaturas
    def _build_thumbnails(self, parent):
        strip = ui.frame(parent, "bg")
        strip.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        ui.label(
            strip,
            "ÚLTIMAS CAPTURAS · clique para carregar no painel · duplo clique amplia",
            kind="small",
        ).pack(anchor="w", pady=(0, 4))
        # Rolagem horizontal garante que todas as 10 capturas fiquem acessíveis
        # em telas estreitas.
        self.thumb_row = ctk.CTkScrollableFrame(
            strip,
            orientation="horizontal",
            fg_color="transparent",
            height=78,
            scrollbar_button_color=BUTTON_BG,
            scrollbar_button_hover_color=BUTTON_HOVER,
        )
        self.thumb_row.pack(fill="x")

    # ------------------------------------------------------------------ ciclo
    def run_cycle(self):
        """Executa a inspeção sem interromper o vídeo ao vivo."""
        result = self.cycle_service.run()

        if result.get("record"):
            record = self.app.history.add_result(result)
            self._last_record = record
            self.app.refresh_header_stats()
            self._show_record(record, refresh=True)

        return result

    def set_status(self, text, color, score=None, threshold=None):
        self.detail_result.configure(text=text, text_color=color)
        if score is not None:
            self.detail_values["Score"].configure(text=str(int(score)))
            if threshold is not None:
                self.detail_values["Limiar"].configure(text=f"{threshold:g}")

    def _use_selected_recipe(self):
        name = self.selected_recipe.get()
        for recipe in self.recipes:
            if recipe["name"] == name:
                self.app.set_active_recipe(recipe)
                break

    def _start_trigger(self):
        trigger = self.config["trigger"]
        self._trigger = TriggerService(self.app, self.io, self.run_cycle, pin=trigger["pin"])
        self._trigger.start()

    # ------------------------------------------------------------------ vídeo
    def _tick(self):
        if not self.running:
            return
        try:
            frame = self.camera.get_frame(timeout=0.05)
            if frame is not None:
                frame = orient_frame(frame, self.config.get("rotate_180", True))
                self._show_frame(frame, overlay_roi=True)
        except tk.TclError:
            self.running = False
            return
        except Exception:
            LOGGER.exception("Falha ao atualizar a prévia")
        try:
            self._after_id = self.canvas.after(FRAME_INTERVAL_MS, self._tick)
        except tk.TclError:
            self.running = False

    def _show_frame(self, frame_bgr, overlay_roi=False):
        if overlay_roi:
            frame_bgr = frame_bgr.copy()
            roi = (self.app.current_recipe or {}).get("roi")
            box = clamp_roi(roi, frame_bgr.shape)
            if box is not None:
                cv2.rectangle(
                    frame_bgr,
                    (box["x1"], box["y1"]),
                    (box["x2"], box["y2"]),
                    (16, 185, 129),
                    2,
                )

        width, height = self._canvas_size()
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        image = ImageOps.contain(Image.fromarray(rgb), (width, height), Image.LANCZOS)
        # tk.Canvas exige PhotoImage; CTkImage só funciona em widgets CTk.
        photo = ImageTk.PhotoImage(image=image)
        self._photo = photo

        center_x, center_y = width // 2, height // 2
        if self._canvas_item is None:
            self._canvas_item = self.canvas.create_image(center_x, center_y, image=photo)
        else:
            self.canvas.itemconfigure(self._canvas_item, image=photo)
            self.canvas.coords(self._canvas_item, center_x, center_y)

    def _canvas_size(self):
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        return (
            width if width > 1 else CANVAS_WIDTH,
            height if height > 1 else CANVAS_HEIGHT,
        )

    # ------------------------------------------------------------------ análise
    def _record_roi(self, record):
        recipe = self.app.current_recipe or {}
        if record.recipe == recipe.get("name"):
            return recipe.get("roi")
        return None

    def _show_record(self, record, refresh=True):
        """Carrega a captura analisada no painel lateral (vídeo continua ao vivo)."""
        self._selected_record = record

        image = record_image(
            record, (PREVIEW_WIDTH, PREVIEW_HEIGHT), overlay_roi=self._record_roi(record)
        )
        self._set_preview(image, empty_text="Imagem não disponível")

        self.detail_result.configure(
            text=record.result, text_color=SUCCESS if record.ok else DANGER
        )
        self._update_details(record)
        self.open_button.configure(state="normal")

        if refresh:
            self.refresh_thumbnails(selected=record)

    def _set_preview(self, image, empty_text="Nenhuma captura ainda"):
        """Recria o conteúdo do preview (evita o bug de image=None no CTkLabel)."""
        for child in self.preview_holder.winfo_children():
            child.destroy()
        self._preview_photo = None

        if image is not None:
            self._preview_photo = ctk.CTkImage(
                light_image=image, dark_image=image, size=image.size
            )
            widget = ctk.CTkLabel(
                self.preview_holder,
                image=self._preview_photo,
                text="",
                fg_color="transparent",
            )
            self.preview_holder.configure(fg_color=CARD)
        else:
            widget = ctk.CTkLabel(
                self.preview_holder,
                text=empty_text,
                text_color=TEXT_DISABLED,
                fg_color="transparent",
                font=ui.font("Segoe UI", 11),
            )
            self.preview_holder.configure(fg_color=INPUT_BG)

        widget.pack(expand=True)
        widget.bind("<Button-1>", lambda _event: self._open_analysis())

    def _open_analysis(self):
        record = self._selected_record or self._last_record
        if record is None:
            return
        AnalysisDialog(self, record, roi=self._record_roi(record))

    def _update_details(self, data):
        def get(key, default="—"):
            if hasattr(data, key):
                return getattr(data, key)
            return data.get(key, default)

        self.detail_values["Receita"].configure(text=str(get("recipe", "—")))
        timestamp = get("timestamp")
        self.detail_values["Horário"].configure(
            text=timestamp.strftime("%H:%M:%S") if hasattr(timestamp, "strftime") else "—"
        )
        self.detail_values["Score"].configure(text=str(get("score", "—")))
        threshold = get("threshold")
        self.detail_values["Limiar"].configure(
            text=f"{threshold:g}" if isinstance(threshold, (int, float)) else "—"
        )
        brightness = get("brightness")
        self.detail_values["Brilho"].configure(
            text=f"{brightness:.0f}" if isinstance(brightness, (int, float)) else "—"
        )
        elapsed = get("elapsed_ms")
        self.detail_values["Tempo"].configure(
            text=f"{elapsed} ms" if isinstance(elapsed, int) and elapsed else "—"
        )

    def refresh_thumbnails(self, selected=None):
        for child in self.thumb_row.winfo_children():
            child.destroy()
        self._thumb_photos.clear()

        selected = selected or self._selected_record
        records = self.app.history.recent(THUMB_COUNT)
        if not records:
            ui.label(self.thumb_row, "Nenhuma captura ainda", kind="small").pack(anchor="w")
            return

        for record in records:
            frame = record.frame_bgr()
            border = PRIMARY if record is selected else BORDER
            item = ctk.CTkFrame(
                self.thumb_row,
                fg_color=CARD,
                corner_radius=6,
                border_width=2,
                border_color=border,
            )
            item.pack(side="left", padx=(0, 6))

            if frame is not None:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = ImageOps.contain(
                    Image.fromarray(rgb), (THUMB_WIDTH - 4, THUMB_HEIGHT - 4), Image.LANCZOS
                )
                photo = ctk.CTkImage(light_image=image, dark_image=image, size=image.size)
                self._thumb_photos.append(photo)
                image_label = ctk.CTkLabel(item, image=photo, text="", fg_color=CARD)
            else:
                image_label = ctk.CTkLabel(
                    item, text="sem imagem", fg_color=INPUT_BG,
                    text_color=TEXT_DISABLED, width=THUMB_WIDTH,
                    height=THUMB_HEIGHT, font=ui.font("Segoe UI", 10),
                )
            image_label.pack()

            caption = ctk.CTkLabel(
                item,
                text=f"{record.time_text} · {'OK' if record.ok else 'NOK'}",
                fg_color=CARD,
                text_color=SUCCESS if record.ok else DANGER,
                font=ui.font("Segoe UI", 10),
                height=18,
            )
            caption.pack(pady=(0, 3))

            for widget in (item, image_label, caption):
                widget.bind("<Button-1>", lambda _event, r=record: self._select(r))
                widget.bind("<Double-Button-1>", lambda _event, r=record: self._select(r, enlarge=True))

    def _select(self, record, enlarge=False):
        """Clique na miniatura: carrega a análise no painel (vídeo segue ao vivo).

        Duplo clique abre a captura em tamanho grande.
        """
        self._show_record(record, refresh=True)
        if enlarge:
            self._open_analysis()

    # ------------------------------------------------------------------ ciclo de vida
    def on_show(self):
        self.config = load_config()
        self.recipes = list_recipes()
        self.recipe_names = [recipe["name"] for recipe in self.recipes]
        self.recipe_combo.configure(values=self.recipe_names)
        self.selected_recipe.set(
            (self.app.current_recipe or {}).get("name", "")
            or (self.recipe_names[0] if self.recipe_names else "")
        )

        backend = self.camera.backend_name
        self.camera_label.configure(text=f"Câmera: {backend}")
        self._loaded_backend = backend

        if self._selected_record is None:
            recent = self.app.history.recent(1)
            if recent:
                self._last_record = recent[0]
                self._show_record(recent[0], refresh=False)

        self.refresh_thumbnails()
        self.app.refresh_header_stats()
        self._start_trigger()

        self.running = True
        if self._after_id is None:
            self._tick()

    def on_history_cleared(self):
        """Volta o painel ao estado inicial quando o histórico é apagado."""
        self._selected_record = None
        self._last_record = None
        self._set_preview(None)
        self.detail_result.configure(text="Aguardando", text_color=TEXT_DIM)
        for value in self.detail_values.values():
            value.configure(text="—")
        self.open_button.configure(state="disabled")
        self.refresh_thumbnails()

    def on_hide(self):
        self.running = False
        if self._trigger is not None:
            self._trigger.stop()
            self._trigger = None
        if self._after_id is not None:
            try:
                self.canvas.after_cancel(self._after_id)
            except tk.TclError:
                pass
            self._after_id = None
