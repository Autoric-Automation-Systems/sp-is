"""Aba de sensores e saídas (I/O) do sistema de inspeção."""
import tkinter as tk

from components import ui
from services.config_service import load_config
from services.io_service import get_io
from styles.theme import *
from .base_tab import BaseTab


class IoTab(BaseTab):
    def __init__(self, parent):
        super().__init__(parent)
        self.io = get_io()
        self.config = load_config()
        inputs, outputs = self.io.pin_map()

        scroll, self.body = ui.scrollable(self.container, bg=CARD)
        scroll.pack(fill="both", expand=True)

        panel = self._make_label_frame(self.body, "Sensores", pack=False)
        panel.pack(fill="x", pady=(0, 12))

        self.sensor_states = {}
        labels = {
            "presence": "Presença de peça",
            "ejection": "Peça na expulsão",
            "trigger": "Trigger",
        }
        for index, (key, text) in enumerate(labels.items()):
            ui.label(panel, text, kind="body").grid(row=index, column=0, sticky="w", pady=4)
            ui.label(panel, f"BCM {inputs[key]}", kind="small").grid(
                row=index, column=1, sticky="w", padx=12, pady=4
            )
            state = tk.Label(panel, text="—", font=FONT_BOLD, bg=CARD, fg=TEXT_DIM, padx=8, pady=2)
            state.grid(row=index, column=2, sticky="e", padx=8)
            self.sensor_states[key] = state
        panel.grid_columnconfigure(2, weight=1)

        outputs_panel = self._make_label_frame(self.body, "Saídas (teste)", pack=False)
        outputs_panel.pack(fill="x", pady=(0, 12))

        self.output_states = {}
        for index, (key, text, command) in enumerate(
            (
                ("ejector", "Expulsor", self.test_ejector),
                ("led", "LED do trigger", self.test_led),
            )
        ):
            ui.label(outputs_panel, text, kind="body").grid(row=index, column=0, sticky="w", pady=4)
            ui.label(outputs_panel, f"BCM {outputs[key]}", kind="small").grid(
                row=index, column=1, sticky="w", padx=12, pady=4
            )
            state = tk.Label(outputs_panel, text="—", font=FONT_BOLD, bg=CARD, fg=TEXT_DIM)
            state.grid(row=index, column=2, sticky="w", padx=8)
            ui.button(outputs_panel, f"Testar {text.lower()}", command=command, size="sm").grid(
                row=index, column=3, sticky="e", padx=8, pady=4
            )
            self.output_states[key] = state
        outputs_panel.grid_columnconfigure(2, weight=1)

        self.message = ui.label(self.body, "", kind="small")
        self.message.pack(anchor="w")

        if self.io.simulated:
            sim = self._make_label_frame(self.body, "Simulação (sem GPIO)", pack=False)
            sim.pack(fill="x", pady=(12, 0))
            self.sim_presence = tk.BooleanVar(value=False)
            self.sim_ejection = tk.BooleanVar(value=False)
            ui.checkbox(
                sim,
                "Simular presença de peça",
                self.sim_presence,
                command=lambda: self.io.set_simulated_input("presence", self.sim_presence.get()),
            ).pack(anchor="w", pady=2)
            ui.checkbox(
                sim,
                "Simular peça na expulsão",
                self.sim_ejection,
                command=lambda: self.io.set_simulated_input("ejection", self.sim_ejection.get()),
            ).pack(anchor="w", pady=2)

        ui.label(
            self.body,
            f"Backend de I/O: {self.io.backend_name}",
            kind="small",
        ).pack(anchor="w", pady=(12, 0))

        self.update()

    def test_ejector(self):
        duration = self.config["ejector"]["time_ms"]
        self.io.pulse_output("ejector", duration)
        self.message.configure(text=f"Pulso de {duration} ms enviado ao expulsor.")

    def test_led(self):
        duration = 300
        self.io.pulse_output("led", duration)
        self.message.configure(text=f"Pulso de {duration} ms enviado ao LED de trigger.")

    def update(self):
        for key, widget in self.sensor_states.items():
            active = self.io.read_input(key)
            widget.configure(
                text="ATIVO" if active else "INATIVO",
                fg=SUCCESS if active else TEXT_DISABLED,
            )

        for key, widget in self.output_states.items():
            active = self.io.read_output(key)
            widget.configure(
                text="LIGADO" if active else "DESLIGADO",
                fg=SUCCESS if active else TEXT_DISABLED,
            )
