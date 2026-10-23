"""Aba de Discos"""
import time
import tkinter as tk
from components import ui
from styles.theme import *
from processes.monitor import SystemMonitor
from .base_tab import BaseTab


class DiskTab(BaseTab):
    def __init__(self, parent):
        super().__init__(parent)

        tk.Label(
            self.container, text="Partições e Uso dos Discos",
            font=FONT_HEADER, fg=PRIMARY, bg=CARD
        ).pack(anchor="w", pady=(0, 16))

        self.disk_container = ui.frame(self.container, "card")
        self.disk_container.pack(fill="both", expand=True)

        self.disk_frames = []
        self._last_partition_check = 0.0
        self._rebuild()

    def _rebuild(self):
        for child in self.disk_container.winfo_children():
            child.destroy()
        self.disk_frames.clear()

        partitions = SystemMonitor.disk_partitions()
        for part in partitions:
            pf = tk.Frame(self.disk_container, bg=CARD, bd=1, relief="solid", highlightbackground=BORDER)
            pf.pack(fill="x", pady=(0, 8), ipadx=12, ipady=8)

            header = ui.frame(pf, "card")
            header.pack(fill="x")
            tk.Label(header, text=f"{part.device}", font=FONT_BOLD, fg=TEXT, bg=CARD).pack(side="left")
            tk.Label(header, text=f"Montagem: {part.mountpoint}", font=FONT_SMALL, fg=TEXT_DIM, bg=CARD).pack(side="right")
            tk.Label(header, text=f"FS: {part.fstype}", font=FONT_SMALL, fg=TEXT_DIM, bg=CARD).pack(side="right", padx=(0, 12))

            bar_f = ui.frame(pf, "card")
            bar_f.pack(fill="x", pady=(6, 2))
            canvas = tk.Canvas(bar_f, height=16, bg=INPUT_BG,
                               highlightthickness=1, highlightbackground=BORDER, bd=0)
            canvas.pack(fill="x")
            fill_rect = canvas.create_rectangle(0, 0, 0, 16, fill=SUCCESS, width=0)

            info = ui.frame(pf, "card")
            info.pack(fill="x")
            used = tk.Label(info, text="Usado: ---", font=FONT_SMALL, fg=TEXT, bg=CARD)
            used.pack(side="left", padx=(0, 16))
            free = tk.Label(info, text="Livre: ---", font=FONT_SMALL, fg=TEXT, bg=CARD)
            free.pack(side="left", padx=(0, 16))
            total = tk.Label(info, text="Total: ---", font=FONT_SMALL, fg=TEXT, bg=CARD)
            total.pack(side="left")
            pct = tk.Label(info, text="---%", font=FONT_SMALL, fg=TEXT_DIM, bg=CARD)
            pct.pack(side="right")

            self.disk_frames.append({
                "part": part,
                "canvas": canvas,
                "fill_rect": fill_rect,
                "used": used,
                "free": free,
                "total": total,
                "pct": pct,
            })

    def _maybe_rebuild(self):
        """Atualiza a lista quando um disco é conectado/removido (a cada 10 s)."""
        now = time.monotonic()
        if now - self._last_partition_check < 10:
            return
        self._last_partition_check = now
        devices = [part.device for part in SystemMonitor.disk_partitions()]
        current = [frame["part"].device for frame in self.disk_frames]
        if devices != current:
            self._rebuild()

    def update(self):
        self._maybe_rebuild()
        fmt = SystemMonitor.format_bytes
        for df in self.disk_frames:
            try:
                usage = SystemMonitor.disk_usage(df["part"].mountpoint)
                pct = usage.percent
                w = df["canvas"].winfo_width()
                df["canvas"].coords(df["fill_rect"], 0, 0, w * pct / 100, 16)
                color = SUCCESS if pct < 50 else (WARNING if pct < 80 else DANGER)
                df["canvas"].itemconfig(df["fill_rect"], fill=color)
                df["used"].configure(text=f"Usado: {fmt(usage.used)}")
                df["free"].configure(text=f"Livre: {fmt(usage.free)}")
                df["total"].configure(text=f"Total: {fmt(usage.total)}")
                df["pct"].configure(text=f"{pct:.1f}%")
            except:
                pass
