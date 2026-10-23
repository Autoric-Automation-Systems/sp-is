"""Aba de CPU"""
import tkinter as tk
import psutil
import platform
from components import ui
from styles.theme import *
from processes.monitor import SystemMonitor
from .base_tab import BaseTab


class CpuTab(BaseTab):
    def __init__(self, parent):
        super().__init__(parent)

        info_frame = self._make_label_frame(self.container, "Informações do Processador")
        cpu_info = [
            ("Modelo", platform.processor() or "Desconhecido"),
            ("Arquitetura", platform.machine()),
            ("Núcleos Físicos", f"{psutil.cpu_count(logical=False)}"),
            ("Núcleos Lógicos", f"{psutil.cpu_count(logical=True)}"),
        ]
        self._make_info_table(info_frame, cpu_info)

        usage_frame = self._make_label_frame(self.container, "Uso da CPU")
        self.cpu_lbl = self._make_header_text(usage_frame, "--- %", fg=SUCCESS)
        self.cpu_canvas, self.cpu_fill = self._make_bar(usage_frame)

        percpu_frame = self._make_label_frame(self.container, "Uso por Núcleo")
        self.percpu_labels = []
        percpu = SystemMonitor.cpu_percent_per_core()
        cols = 4
        for i, p in enumerate(percpu):
            row_f = ui.frame(percpu_frame, "card")
            row_f.grid(row=i // cols, column=i % cols, sticky="w", padx=8, pady=4)
            tk.Label(row_f, text=f"Núcleo {i}:", font=FONT_BOLD, fg=TEXT_DIM, bg=CARD).pack(side="left")
            val = tk.Label(row_f, text=f"{p:.1f}%", font=FONT, fg=TEXT, bg=CARD)
            val.pack(side="left", padx=(6, 0))
            self.percpu_labels.append(val)

    def update(self):
        pct = SystemMonitor.cpu_percent()
        color = SUCCESS if pct < 50 else (WARNING if pct < 80 else DANGER)
        self.cpu_lbl.configure(text=f"{pct:.1f}%", text_color=color)
        w = self.cpu_canvas.winfo_width()
        self.cpu_canvas.coords(self.cpu_fill, 0, 0, w * pct / 100, 20)
        self.cpu_canvas.itemconfig(self.cpu_fill, fill=color)

        percpu = SystemMonitor.cpu_percent_per_core()
        for i, val in enumerate(self.percpu_labels):
            if i < len(percpu):
                val.configure(text=f"{percpu[i]:.1f}%")
