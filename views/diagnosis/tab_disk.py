"""Aba de Discos"""
import tkinter as tk
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

        self.disk_container = tk.Frame(self.container, bg=CARD)
        self.disk_container.pack(fill="both", expand=True)

        self.disk_frames = []
        self._rebuild()

    def _rebuild(self):
        for child in self.disk_container.winfo_children():
            child.destroy()
        self.disk_frames.clear()

        partitions = SystemMonitor.disk_partitions()
        for part in partitions:
            pf = tk.Frame(self.disk_container, bg=CARD, bd=1, relief="solid", highlightbackground=BORDER)
            pf.pack(fill="x", pady=(0, 8), ipadx=12, ipady=8)

            header = tk.Frame(pf, bg=CARD)
            header.pack(fill="x")
            tk.Label(header, text=f"{part.device}", font=FONT_BOLD, fg=TEXT, bg=CARD).pack(side="left")
            tk.Label(header, text=f"Montagem: {part.mountpoint}", font=FONT_SMALL, fg=TEXT_DIM, bg=CARD).pack(side="right")
            tk.Label(header, text=f"FS: {part.fstype}", font=FONT_SMALL, fg=TEXT_DIM, bg=CARD).pack(side="right", padx=(0, 12))

            bar_f = tk.Frame(pf, bg=CARD)
            bar_f.pack(fill="x", pady=(6, 2))
            canvas = tk.Canvas(bar_f, height=16, bg=INPUT_BG,
                               highlightthickness=1, highlightbackground=BORDER, bd=0)
            canvas.pack(fill="x")
            fill_rect = canvas.create_rectangle(0, 0, 0, 16, fill=SUCCESS, width=0)

            info = tk.Frame(pf, bg=CARD)
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

    def update(self):
        fmt = SystemMonitor.format_bytes
        for df in self.disk_frames:
            try:
                usage = SystemMonitor.disk_usage(df["part"].mountpoint)
                pct = usage.percent
                w = df["canvas"].winfo_width()
                df["canvas"].coords(df["fill_rect"], 0, 0, w * pct / 100, 16)
                color = SUCCESS if pct < 50 else (WARNING if pct < 80 else DANGER)
                df["canvas"].itemconfig(df["fill_rect"], fill=color)
                df["used"].config(text=f"Usado: {fmt(usage.used)}")
                df["free"].config(text=f"Livre: {fmt(usage.free)}")
                df["total"].config(text=f"Total: {fmt(usage.total)}")
                df["pct"].config(text=f"{pct:.1f}%")
            except:
                pass
