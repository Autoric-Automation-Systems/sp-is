"""Tela de Configurações: câmera, trigger, expulsador e mapeamento de I/O."""
import copy
import logging
import os
import tkinter as tk
from tkinter import messagebox

from components import ui
from components.camera_view import current_backend_name, list_available_cameras, restart_camera
from services.config_service import load_config, save_config
from services.io_service import AVAILABLE_BCM_PINS, get_io, restart_io
from styles.theme import *
from views.base_page import Page

LOGGER = logging.getLogger(__name__)


class SettingsPage(Page):
    route = "settings"

    def build(self):
        self.config = load_config()
        self._camera_map = {}

        container, inner = ui.scrollable(self, bg=BG)
        container.pack(fill="both", expand=True)

        body = ui.frame(inner, "bg")
        body.pack(fill="both", expand=True, padx=20, pady=12)

        ui.label(body, "CONFIGURAÇÕES", kind="title").pack(anchor="w")
        ui.label(
            body,
            "Câmera, trigger, expulsador e mapeamento de entradas/saídas",
            kind="small",
        ).pack(anchor="w", pady=(0, 12))

        columns = ui.frame(body, "bg")
        columns.pack(fill="both", expand=True)
        columns.grid_columnconfigure(0, weight=1, uniform="settings")
        columns.grid_columnconfigure(1, weight=1, uniform="settings")

        left = ui.frame(columns, "bg")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        right = ui.frame(columns, "bg")
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        self._build_camera(left)
        self._build_trigger(left)
        self._build_ejector(right)
        self._build_io(right)

        actions = ui.frame(body, "bg")
        actions.pack(fill="x", pady=(8, 24))
        ui.button(
            actions,
            "Salvar configurações",
            command=self.save,
            variant="primary",
            size="lg",
        ).pack(side="right")

    def on_show(self):
        self.app.refresh_header_stats()
        self.config = load_config()
        self._sync_fields()

    def _sync_fields(self):
        self.refresh_cameras()
        self.rotate_var.set(bool(self.config.get("rotate_180", True)))
        self.trigger_pin_var.set(str(self.config["trigger"]["pin"]))
        self.ejector_var.set(f'{self.config["ejector"]["time_ms"]:g}')
        for key, variable in self.io_vars.items():
            variable.set(str(self.config["io"][key]))
        self.active_high_var.set(bool(self.config["io"].get("active_high", True)))

    # ------------------------------------------------------------------ câmera
    def _build_camera(self, parent):
        panel = ui.panel(
            parent,
            title="Câmera",
            subtitle="Selecione a fonte de vídeo usada na inspeção e no cadastro de receitas.",
            pack=False,
        )
        panel.pack(fill="x", pady=(0, 12))

        row = ui.frame(panel.content, "card")
        row.pack(fill="x", pady=4)

        self.camera_var = tk.StringVar()
        self.camera_dropdown = ui.dropdown(
            row, self.camera_var, [], width=38, command=self._on_camera_selected
        )
        self.camera_dropdown.pack(side="left")
        ui.button(row, "Atualizar", command=self.refresh_cameras, size="sm").pack(
            side="left", padx=(8, 0)
        )

        self.rotate_var = tk.BooleanVar(value=bool(self.config.get("rotate_180", True)))
        ui.checkbox(
            panel.content,
            "Girar a imagem 180° (câmera montada invertida)",
            self.rotate_var,
            command=self._on_rotate_changed,
        ).pack(anchor="w", pady=(8, 0))

        self.camera_status = ui.label(panel.content, "", kind="small")
        self.camera_status.pack(anchor="w", pady=(8, 0))

        self.refresh_cameras()

        if os.environ.get("SPIS_CAMERA"):
            ui.label(
                panel.content,
                f"Atenção: SPIS_CAMERA={os.environ['SPIS_CAMERA']} tem precedência sobre esta configuração.",
                kind="small",
                fg=WARNING,
            ).pack(anchor="w", pady=(4, 0))

    def refresh_cameras(self):
        cameras = list_available_cameras()
        configured = self.config.get("camera_source", "auto")

        sources = [camera["source"] for camera in cameras]
        if configured and configured not in sources:
            cameras.insert(
                0, {"source": configured, "label": f"{configured} (configurada, não detectada)"}
            )

        self._camera_map = {camera["label"]: camera["source"] for camera in cameras}
        labels = list(self._camera_map)
        self.camera_dropdown.configure(values=labels)

        current = next(
            (label for label, source in self._camera_map.items() if source == configured),
            labels[0] if labels else "",
        )
        self.camera_var.set(current)

        self._update_camera_status()

    def _update_camera_status(self):
        in_use = current_backend_name()
        configured = self.config.get("camera_source", "auto")
        text = f"Fonte em uso: {in_use or 'não iniciada'}"
        if in_use == "synthetic" and configured != "synthetic":
            text += f" (fallback: {configured} indisponível)"
        self.camera_status.configure(text=text)

    def _camera_source_from_label(self, label=None):
        label = label if label is not None else self.camera_var.get()
        return self._camera_map.get(label)

    def _select_camera_label(self, source):
        for label, value in self._camera_map.items():
            if value == source:
                self.camera_var.set(label)
                return

    def _on_camera_selected(self, label):
        """Aplica a troca de câmera imediatamente, sem depender do botão Salvar."""
        source = self._camera_source_from_label(label)
        if not source:
            return
        self._apply_camera(source)

    def _apply_camera(self, source, force=False):
        previous = self.config.get("camera_source", "auto")
        if not force and source == previous and current_backend_name() is not None:
            self._update_camera_status()
            return True

        try:
            backend = restart_camera(source)
        except Exception as exc:
            LOGGER.exception("Falha ao iniciar a câmera %s", source)
            messagebox.showerror(
                "Câmera",
                f"Não foi possível iniciar a fonte selecionada:\n{exc}",
                parent=self,
            )
            self._select_camera_label(previous)
            self._update_camera_status()
            return False

        self.config["camera_source"] = source
        save_config(self.config)
        self.config = load_config()
        self._select_camera_label(source)
        self._update_camera_status()
        LOGGER.info("Fonte de vídeo alterada para %s (%s)", source, backend)
        return True

    def _on_rotate_changed(self):
        self.config["rotate_180"] = bool(self.rotate_var.get())
        save_config(self.config)
        self.config = load_config()

    # ------------------------------------------------------------------ trigger
    def _build_trigger(self, parent):
        panel = ui.panel(
            parent,
            title="Trigger",
            subtitle="O botão na tela Principal é sempre a ação padrão.",
            pack=False,
        )
        panel.pack(fill="x", pady=(0, 12))

        pin_row = ui.frame(panel.content, "card")
        pin_row.pack(fill="x", pady=4)
        ui.label(pin_row, "Entrada de trigger (BCM):", kind="body").pack(side="left")
        self.trigger_pin_var = tk.StringVar(value=str(self.config["trigger"]["pin"]))
        self.trigger_pin = ui.dropdown(
            pin_row,
            self.trigger_pin_var,
            [str(pin) for pin in AVAILABLE_BCM_PINS],
            width=8,
        )
        self.trigger_pin.pack(side="left", padx=(8, 0))
        ui.label(
            panel.content,
            "A entrada é monitorada em paralelo e dispara um ciclo ao ir para nível alto.",
            kind="small",
        ).pack(anchor="w", pady=(4, 0))

    # ------------------------------------------------------------------ expulsador
    def _build_ejector(self, parent):
        panel = ui.panel(
            parent,
            title="Expulsador",
            subtitle="Pulso aplicado na saída do expulsor quando a peça é reprovada.",
            pack=False,
        )
        panel.pack(fill="x", pady=(0, 12))

        row = ui.frame(panel.content, "card")
        row.pack(fill="x", pady=4)
        ui.label(row, "Tempo de expulsão:", kind="body").pack(side="left")
        self.ejector_var = tk.StringVar(value=f'{self.config["ejector"]["time_ms"]:g}')
        ui.entry(row, self.ejector_var, width=8, justify="center").pack(
            side="left", padx=(8, 4)
        )
        ui.label(row, "ms", kind="muted").pack(side="left")

    # ------------------------------------------------------------------ io
    def _build_io(self, parent):
        panel = ui.panel(
            parent,
            title="Entradas e saídas (I/O)",
            subtitle="Pinos BCM usados pelos sensores e saídas físicas.",
            pack=False,
        )
        panel.pack(fill="x", pady=(0, 12))

        io_cfg = self.config["io"]
        self.io_vars = {}
        rows = [
            ("presence_pin", "Sensor de presença de peça"),
            ("ejection_pin", "Sensor de peça na expulsão"),
            ("ejector_pin", "Saída do expulsor"),
            ("led_pin", "Saída do LED de trigger"),
        ]

        grid = ui.frame(panel.content, "card")
        grid.pack(fill="x")
        for index, (key, text) in enumerate(rows):
            ui.label(grid, text, kind="body").grid(
                row=index, column=0, sticky="w", pady=4
            )
            variable = tk.StringVar(value=str(io_cfg[key]))
            ui.dropdown(
                grid, variable, [str(pin) for pin in AVAILABLE_BCM_PINS], width=8
            ).grid(row=index, column=1, sticky="w", padx=(12, 0), pady=4)
            self.io_vars[key] = variable

        self.active_high_var = tk.BooleanVar(value=io_cfg.get("active_high", True))
        ui.checkbox(
            panel.content,
            "Saídas ativas em nível alto",
            self.active_high_var,
        ).pack(anchor="w", pady=(8, 0))

        try:
            backend = get_io().backend_name
        except Exception as exc:
            backend = f"indisponível ({exc})"
        ui.label(panel.content, f"Backend de I/O em uso: {backend}", kind="small").pack(
            anchor="w", pady=(6, 0)
        )

    # ------------------------------------------------------------------ salvar
    def save(self):
        try:
            ejector_ms = int(self.ejector_var.get())
            if ejector_ms < 0:
                raise ValueError
        except (TypeError, ValueError):
            messagebox.showerror("Erro", "Tempo de expulsão deve ser um inteiro em ms.")
            return

        camera_source = self._camera_map.get(self.camera_var.get(), self.config["camera_source"])

        previous = copy.deepcopy(self.config)
        config = copy.deepcopy(self.config)
        config["camera_source"] = camera_source
        config["rotate_180"] = bool(self.rotate_var.get())
        config["trigger"] = {"pin": int(self.trigger_pin_var.get())}
        config["ejector"] = {"time_ms": ejector_ms}
        config["io"] = {
            "presence_pin": int(self.io_vars["presence_pin"].get()),
            "ejection_pin": int(self.io_vars["ejection_pin"].get()),
            "ejector_pin": int(self.io_vars["ejector_pin"].get()),
            "led_pin": int(self.io_vars["led_pin"].get()),
            "active_high": bool(self.active_high_var.get()),
        }

        pin_numbers = [
            config["io"][key]
            for key in ("presence_pin", "ejection_pin", "ejector_pin", "led_pin")
        ]
        if len(pin_numbers) != len(set(pin_numbers)):
            messagebox.showerror("Erro", "Cada entrada/saída deve usar um pino diferente.")
            return

        io_changed = config["io"] != previous["io"]
        camera_changed = camera_source != previous["camera_source"]

        save_config(config)
        self.config = load_config()

        if camera_changed and not self._apply_camera(camera_source, force=True):
            return

        if io_changed:
            try:
                restart_io()
            except Exception as exc:
                LOGGER.exception("Falha ao reiniciar o I/O")
                messagebox.showerror("Erro", f"Falha ao configurar o I/O:\n{exc}")
                return

        messagebox.showinfo("Configurações", "Configurações salvas com sucesso.")
