"""Aba Sistema - SO, sensores, portas fisicas, camera, processos"""
import tkinter as tk
from styles.theme import *
from processes.monitor import SystemMonitor
from processes.gpio_checker import GpioChecker
from processes.camera_checker import CameraChecker
from .base_tab import BaseTab


class SystemTab(BaseTab):
    def __init__(self, parent):
        super().__init__(parent)

        # Scroll
        canvas = tk.Canvas(self.container, bg=CARD, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.container, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=CARD)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Coluna esquerda
        left = tk.Frame(scroll_frame, bg=CARD)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))

        sof = self._make_label_frame(left, "Sistema Operacional", pack=False)
        sof.pack(fill="x", pady=(0, 8))
        info = SystemMonitor.system_info()
        up = SystemMonitor.format_uptime(info["uptime_segundos"])
        self._make_info_table(sof, [
            ("Sistema", info["sistema"]), ("Versao", info["versao"]),
            ("Arquitetura", info["arquitetura"]), ("Hostname", info["hostname"]),
            ("Processador", info["processador"]), ("Tempo de Atividade", up),
        ])

        sf = self._make_label_frame(left, "Sensores da Placa", pack=False)
        sf.pack(fill="x", pady=(0, 8))
        self.temp_lbl = tk.Label(sf, text="Temperatura CPU: ---", font=FONT, fg=TEXT, bg=CARD)
        self.temp_lbl.pack(anchor="w", pady=2)
        self.freq_lbl = tk.Label(sf, text="Frequencia CPU: ---", font=FONT, fg=TEXT, bg=CARD)
        self.freq_lbl.pack(anchor="w", pady=2)
        self.volt_lbl = tk.Label(sf, text="Voltagem Core: ---", font=FONT, fg=TEXT, bg=CARD)
        self.volt_lbl.pack(anchor="w", pady=2)
        self.throttle_lbl = tk.Label(sf, text="Throttling: ---", font=FONT, fg=TEXT, bg=CARD)
        self.throttle_lbl.pack(anchor="w", pady=2)

        pf = self._make_label_frame(left, "Portas Fisicas", pack=False)
        pf.pack(fill="x", pady=(0, 8))
        self.portas_labels = {}
        for nome in ["USB", "HDMI", "Ethernet"]:
            f = tk.Frame(pf, bg=CARD)
            f.pack(fill="x", pady=2)
            tk.Label(f, text=nome, font=FONT_BOLD, fg=TEXT_DIM, bg=CARD, width=14, anchor="w").pack(side="left")
            lbl = tk.Label(f, text="---", font=FONT, fg=TEXT, bg=CARD)
            lbl.pack(side="left")
            self.portas_labels[nome] = lbl

        cf = self._make_label_frame(left, "Camera", pack=False)
        cf.pack(fill="x", pady=(0, 8))
        self.cam_labels = {}
        for m in ["libcamera", "raspistill", "opencv"]:
            f = tk.Frame(cf, bg=CARD)
            f.pack(fill="x", pady=1)
            tk.Label(f, text=m, font=FONT_BOLD, fg=TEXT_DIM, bg=CARD, width=14, anchor="w").pack(side="left")
            lbl = tk.Label(f, text="---", font=FONT, fg=TEXT, bg=CARD)
            lbl.pack(side="left")
            self.cam_labels[m] = lbl

        # Coluna direita
        right = tk.Frame(scroll_frame, bg=CARD)
        right.pack(side="right", fill="both", expand=True, padx=(8, 0))

        pcf = self._make_label_frame(right, "Processos (Top 10 CPU)", pack=False)
        pcf.pack(fill="both", expand=True)

        cols = tk.Frame(pcf, bg=CARD)
        cols.pack(fill="x", pady=4)
        for j, (txt, w) in enumerate([("PID", 8), ("Nome", 20), ("CPU%", 8), ("Mem%", 8)]):
            tk.Label(cols, text=txt, font=FONT_BOLD, fg=TEXT_DIM, bg=CARD, width=w, anchor="w").grid(row=0, column=j, padx=2, pady=2)

        self.proc_labels = []
        for i in range(1, 11):
            pid = tk.Label(cols, text="-", font=FONT_SMALL, fg=TEXT_DIM, bg=CARD, width=8, anchor="w")
            pid.grid(row=i, column=0, padx=2, pady=1, sticky="w")
            name = tk.Label(cols, text="-", font=FONT_SMALL, fg=TEXT, bg=CARD, width=20, anchor="w")
            name.grid(row=i, column=1, padx=2, pady=1, sticky="w")
            cpu = tk.Label(cols, text="-", font=FONT_SMALL, fg=TEXT, bg=CARD, width=8, anchor="e")
            cpu.grid(row=i, column=2, padx=2, pady=1, sticky="e")
            mem = tk.Label(cols, text="-", font=FONT_SMALL, fg=TEXT, bg=CARD, width=8, anchor="e")
            mem.grid(row=i, column=3, padx=2, pady=1, sticky="e")
            self.proc_labels.append((pid, name, cpu, mem))

    def update(self):
        temp = GpioChecker.temperatura_cpu()
        if temp is not None:
            cor = SUCCESS if temp < 60 else (WARNING if temp < 75 else DANGER)
            self.temp_lbl.config(text=f"Temperatura CPU: {temp:.1f} C", fg=cor)
        freq = GpioChecker.frequencia_cpu()
        if freq is not None:
            self.freq_lbl.config(text=f"Frequencia CPU: {freq:.0f} MHz")
        volt = GpioChecker.voltagem_cpu()
        if volt:
            self.volt_lbl.config(text=f"Voltagem Core: {volt}")
        throttle = GpioChecker.throttled_status()
        if throttle:
            self.throttle_lbl.config(text=f"Throttling: {throttle}")

        usb = GpioChecker.usb_ports()
        self.portas_labels["USB"].config(text=f"{usb} dispositivo(s)", fg=SUCCESS if usb else TEXT_DIM)
        hok, hmsg = GpioChecker.hdmi_status()
        self.portas_labels["HDMI"].config(text=hmsg, fg=SUCCESS if hok else TEXT_DIM)
        eok, emsg = GpioChecker.ethernet_status()
        self.portas_labels["Ethernet"].config(text=emsg, fg=SUCCESS if eok else TEXT_DIM)

        cam = CameraChecker.check()
        for m, lbl in self.cam_labels.items():
            s = cam.get(m, "?")
            if "Dispon" in str(s) or "OK" in str(s):
                cor = SUCCESS
            elif "Nao" in str(s) or "Erro" in str(s):
                cor = TEXT_DISABLED
            else:
                cor = TEXT_DIM
            lbl.config(text=str(s), fg=cor)

        try:
            procs = SystemMonitor.top_processes(10)
            for i, (pid_lbl, name_lbl, cpu_lbl, mem_lbl) in enumerate(self.proc_labels):
                if i < len(procs):
                    p = procs[i]
                    pid_lbl.config(text=str(p["pid"]))
                    name_lbl.config(text=(p["name"] or "-")[:18])
                    cpu_lbl.config(text=f"{(p.get('cpu_percent') or 0):.1f}%")
                    mem_lbl.config(text=f"{(p.get('memory_percent') or 0):.1f}%")
                else:
                    pid_lbl.config(text="-")
                    name_lbl.config(text="-")
                    cpu_lbl.config(text="-")
                    mem_lbl.config(text="-")
        except:
            pass
