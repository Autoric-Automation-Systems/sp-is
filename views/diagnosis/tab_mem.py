"""Aba de Memória"""
import tkinter as tk
from components import ui
from styles.theme import *
from processes.monitor import SystemMonitor
from .base_tab import BaseTab


class MemTab(BaseTab):
    def __init__(self, parent):
        super().__init__(parent)

        ram_frame = self._make_label_frame(self.container, "Memória RAM")
        self.ram_lbl = self._make_header_text(ram_frame, "--- %", fg=SUCCESS)
        self.ram_canvas, self.ram_fill = self._make_bar(ram_frame, fill_color=PRIMARY)

        info_f = ui.frame(ram_frame, "card")
        info_f.pack(fill="x", pady=6)
        self.ram_used = tk.Label(info_f, text="Usado: ---", font=FONT, fg=TEXT, bg=CARD)
        self.ram_used.pack(side="left", padx=(0, 24))
        self.ram_total = tk.Label(info_f, text="Total: ---", font=FONT, fg=TEXT, bg=CARD)
        self.ram_total.pack(side="left", padx=(0, 24))
        self.ram_avail = tk.Label(info_f, text="Disponível: ---", font=FONT, fg=TEXT, bg=CARD)
        self.ram_avail.pack(side="left")

        swap_frame = self._make_label_frame(self.container, "Memória Swap", fg=WARNING)
        self.swap_lbl = self._make_header_text(swap_frame, "--- %", font_size=24, fg=TEXT_DIM)
        self.swap_canvas, self.swap_fill = self._make_bar(swap_frame, height=16, fill_color=WARNING)

        sw_info = ui.frame(swap_frame, "card")
        sw_info.pack(fill="x", pady=4)
        self.swap_used = tk.Label(sw_info, text="Usado: ---", font=FONT, fg=TEXT, bg=CARD)
        self.swap_used.pack(side="left", padx=(0, 24))
        self.swap_total = tk.Label(sw_info, text="Total: ---", font=FONT, fg=TEXT, bg=CARD)
        self.swap_total.pack(side="left")

    def update(self):
        mem = SystemMonitor.ram()
        pct = mem.percent
        color = SUCCESS if pct < 50 else (WARNING if pct < 80 else DANGER)
        self.ram_lbl.configure(text=f"{pct:.1f}%", text_color=color)
        w = self.ram_canvas.winfo_width()
        self.ram_canvas.coords(self.ram_fill, 0, 0, w * pct / 100, 20)
        self.ram_canvas.itemconfig(self.ram_fill, fill=color)

        fmt = SystemMonitor.format_bytes
        self.ram_used.configure(text=f"Usado: {fmt(mem.used)}")
        self.ram_total.configure(text=f"Total: {fmt(mem.total)}")
        self.ram_avail.configure(text=f"Disponível: {fmt(mem.available)}")

        swap = SystemMonitor.swap()
        spct = swap.percent
        self.swap_lbl.configure(text=f"{spct:.1f}%")
        sw = self.swap_canvas.winfo_width()
        self.swap_canvas.coords(self.swap_fill, 0, 0, sw * spct / 100, 16)
        self.swap_canvas.itemconfig(self.swap_fill, fill=WARNING if spct > 0 else TEXT_DISABLED)
        self.swap_used.configure(text=f"Usado: {fmt(swap.used)}")
        self.swap_total.configure(text=f"Total: {fmt(swap.total)}")
