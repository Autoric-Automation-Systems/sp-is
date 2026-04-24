import tkinter as tk
from tkinter import ttk
import psutil
import platform
import time
import os
import socket
from components.layout import BaseLayout
from styles.theme import *

class DiagnosisView:
    def __init__(self, parent, app):
        self.app = app
        layout = BaseLayout(parent, app)
        layout.content.configure(bg=BG)

        # -------- HEADER DA VIEW --------
        header_frame = tk.Frame(layout.content, bg=BG)
        header_frame.pack(fill="x", padx=32, pady=(20, 0))

        tk.Label(
            header_frame,
            text="DIAGNÓSTICO DO SISTEMA",
            font=FONT_TITLE,
            fg=TEXT,
            bg=BG
        ).pack(anchor="w")

        tk.Label(
            header_frame,
            text="Monitoramento de hardware, sistema e rede da máquina",
            font=FONT,
            fg=TEXT_DIM,
            bg=BG
        ).pack(anchor="w", pady=(4, 0))

        # -------- NOTEBOOK (ABAS) --------
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "TNotebook",
            background=BG,
            borderwidth=0,
            padding=0
        )
        style.configure(
            "TNotebook.Tab",
            background=BUTTON_BG,
            foreground=TEXT_DIM,
            font=FONT_BOLD,
            padding=[16, 8],
            borderwidth=0,
            focuscolor="none"
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", CARD), ("active", BUTTON_HOVER)],
            foreground=[("selected", PRIMARY), ("active", TEXT)]
        )
        style.configure(
            "TFrame",
            background=CARD
        )

        notebook = ttk.Notebook(layout.content, style="TNotebook")
        notebook.pack(fill="both", expand=True, padx=32, pady=20)

        # -------- CRIAÇÃO DAS ABAS --------
        self.tab_cpu = ttk.Frame(notebook)
        self.tab_mem = ttk.Frame(notebook)
        self.tab_disk = ttk.Frame(notebook)
        self.tab_pinout = ttk.Frame(notebook)
        self.tab_network = ttk.Frame(notebook)
        self.tab_system = ttk.Frame(notebook)

        notebook.add(self.tab_cpu, text="CPU")
        notebook.add(self.tab_mem, text="Memória")
        notebook.add(self.tab_disk, text="HD / Disco")
        notebook.add(self.tab_pinout, text="Pinout / Portas")
        notebook.add(self.tab_network, text="Rede")
        notebook.add(self.tab_system, text="Sistema")

        # -------- CONTEÚDO DE CADA ABA --------
        self._build_cpu_tab()
        self._build_mem_tab()
        self._build_disk_tab()
        self._build_pinout_tab()
        self._build_network_tab()
        self._build_system_tab()

        # -------- LOOP DE ATUALIZAÇÃO --------
        self.running = True
        self._update_all()

    # ========== ABA CPU ==========
    def _build_cpu_tab(self):
        container = tk.Frame(self.tab_cpu, bg=CARD)
        container.pack(fill="both", expand=True, padx=24, pady=24)

        # Informações do processador
        info_frame = tk.LabelFrame(container, text="Informações do Processador",
                                   font=FONT_HEADER, fg=PRIMARY, bg=CARD, bd=0,
                                   padx=16, pady=12)
        info_frame.pack(fill="x", pady=(0, 16))

        cpu_info = [
            ("Modelo", platform.processor() or "Desconhecido"),
            ("Arquitetura", platform.machine()),
            ("Núcleos Físicos", f"{psutil.cpu_count(logical=False)}"),
            ("Núcleos Lógicos", f"{psutil.cpu_count(logical=True)}"),
        ]
        for i, (label, value) in enumerate(cpu_info):
            tk.Label(info_frame, text=f"{label}:", font=FONT_BOLD, fg=TEXT_DIM, bg=CARD).grid(row=i, column=0, sticky="w", pady=3)
            tk.Label(info_frame, text=value, font=FONT, fg=TEXT, bg=CARD).grid(row=i, column=1, sticky="w", padx=(12, 0), pady=3)

        # Uso da CPU
        usage_frame = tk.LabelFrame(container, text="Uso da CPU",
                                    font=FONT_HEADER, fg=PRIMARY, bg=CARD, bd=0,
                                    padx=16, pady=12)
        usage_frame.pack(fill="x", pady=(0, 16))

        self.cpu_percent_label = tk.Label(usage_frame, text="--- %", font=("Segoe UI", 32, "bold"),
                                          fg=SUCCESS, bg=CARD)
        self.cpu_percent_label.pack(pady=10)

        # Barra de progresso manual (canvas)
        self.cpu_bar_canvas = tk.Canvas(usage_frame, height=20, bg=INPUT_BG,
                                        highlightthickness=1, highlightbackground=BORDER, bd=0)
        self.cpu_bar_canvas.pack(fill="x", pady=(0, 8))
        self.cpu_bar_fill = self.cpu_bar_canvas.create_rectangle(0, 0, 0, 20, fill=SUCCESS, width=0)

        # Detalhamento por núcleo
        percpu_frame = tk.LabelFrame(container, text="Uso por Núcleo",
                                     font=FONT_HEADER, fg=PRIMARY, bg=CARD, bd=0,
                                     padx=16, pady=12)
        percpu_frame.pack(fill="x")

        self.percpu_labels = []
        percpu_values = psutil.cpu_percent(percpu=True)
        cols = 4
        for i, p in enumerate(percpu_values):
            row_frame = tk.Frame(percpu_frame, bg=CARD)
            row_frame.grid(row=i // cols, column=i % cols, sticky="w", padx=8, pady=4)

            lbl = tk.Label(row_frame, text=f"Núcleo {i}:", font=FONT_BOLD, fg=TEXT_DIM, bg=CARD)
            lbl.pack(side="left")
            val = tk.Label(row_frame, text=f"{p:.1f}%", font=FONT, fg=TEXT, bg=CARD)
            val.pack(side="left", padx=(6, 0))
            self.percpu_labels.append(val)

    # ========== ABA MEMÓRIA ==========
    def _build_mem_tab(self):
        container = tk.Frame(self.tab_mem, bg=CARD)
        container.pack(fill="both", expand=True, padx=24, pady=24)

        # Memória RAM
        ram_frame = tk.LabelFrame(container, text="Memória RAM",
                                  font=FONT_HEADER, fg=PRIMARY, bg=CARD, bd=0,
                                  padx=16, pady=12)
        ram_frame.pack(fill="x", pady=(0, 16))

        self.ram_percent_label = tk.Label(ram_frame, text="--- %", font=("Segoe UI", 32, "bold"),
                                          fg=SUCCESS, bg=CARD)
        self.ram_percent_label.pack(pady=10)

        self.ram_bar_canvas = tk.Canvas(ram_frame, height=20, bg=INPUT_BG,
                                        highlightthickness=1, highlightbackground=BORDER, bd=0)
        self.ram_bar_canvas.pack(fill="x", pady=(0, 8))
        self.ram_bar_fill = self.ram_bar_canvas.create_rectangle(0, 0, 0, 20, fill=PRIMARY, width=0)

        ram_info_frame = tk.Frame(ram_frame, bg=CARD)
        ram_info_frame.pack(fill="x", pady=6)

        self.ram_used_label = tk.Label(ram_info_frame, text="Usado: ---", font=FONT, fg=TEXT, bg=CARD)
        self.ram_used_label.pack(side="left", padx=(0, 24))
        self.ram_total_label = tk.Label(ram_info_frame, text="Total: ---", font=FONT, fg=TEXT, bg=CARD)
        self.ram_total_label.pack(side="left", padx=(0, 24))
        self.ram_avail_label = tk.Label(ram_info_frame, text="Disponível: ---", font=FONT, fg=TEXT, bg=CARD)
        self.ram_avail_label.pack(side="left")

        # Memória SWAP
        swap_frame = tk.LabelFrame(container, text="Memória Swap",
                                   font=FONT_HEADER, fg=WARNING, bg=CARD, bd=0,
                                   padx=16, pady=12)
        swap_frame.pack(fill="x")

        self.swap_percent_label = tk.Label(swap_frame, text="--- %", font=("Segoe UI", 24, "bold"),
                                           fg=TEXT_DIM, bg=CARD)
        self.swap_percent_label.pack(pady=6)

        self.swap_bar_canvas = tk.Canvas(swap_frame, height=16, bg=INPUT_BG,
                                         highlightthickness=1, highlightbackground=BORDER, bd=0)
        self.swap_bar_canvas.pack(fill="x", pady=(0, 6))
        self.swap_bar_fill = self.swap_bar_canvas.create_rectangle(0, 0, 0, 16, fill=WARNING, width=0)

        swap_info_frame = tk.Frame(swap_frame, bg=CARD)
        swap_info_frame.pack(fill="x", pady=4)
        self.swap_used_label = tk.Label(swap_info_frame, text="Usado: ---", font=FONT, fg=TEXT, bg=CARD)
        self.swap_used_label.pack(side="left", padx=(0, 24))
        self.swap_total_label = tk.Label(swap_info_frame, text="Total: ---", font=FONT, fg=TEXT, bg=CARD)
        self.swap_total_label.pack(side="left")

    # ========== ABA DISCO ==========
    def _build_disk_tab(self):
        container = tk.Frame(self.tab_disk, bg=CARD)
        container.pack(fill="both", expand=True, padx=24, pady=24)

        # Lista partições
        self.disk_frames = []
        partitions = psutil.disk_partitions()

        title = tk.Label(container, text="Partições e Uso dos Discos",
                         font=FONT_HEADER, fg=PRIMARY, bg=CARD)
        title.pack(anchor="w", pady=(0, 16))

        self.disk_container = tk.Frame(container, bg=CARD)
        self.disk_container.pack(fill="both", expand=True)

        for i, part in enumerate(partitions):
            part_frame = tk.Frame(self.disk_container, bg=CARD, bd=1, relief="solid", highlightbackground=BORDER)
            part_frame.pack(fill="x", pady=(0, 8), ipadx=12, ipady=8)

            # Cabeçalho da partição
            header = tk.Frame(part_frame, bg=CARD)
            header.pack(fill="x")
            tk.Label(header, text=f"🔹 {part.device}", font=FONT_BOLD, fg=TEXT, bg=CARD).pack(side="left")
            tk.Label(header, text=f"Montagem: {part.mountpoint}", font=FONT_SMALL, fg=TEXT_DIM, bg=CARD).pack(side="right")
            tk.Label(header, text=f"FS: {part.fstype}", font=FONT_SMALL, fg=TEXT_DIM, bg=CARD).pack(side="right", padx=(0, 12))

            # Barra
            bar_frame = tk.Frame(part_frame, bg=CARD)
            bar_frame.pack(fill="x", pady=(6, 2))
            canvas = tk.Canvas(bar_frame, height=16, bg=INPUT_BG,
                               highlightthickness=1, highlightbackground=BORDER, bd=0)
            canvas.pack(fill="x")
            fill_rect = canvas.create_rectangle(0, 0, 0, 16, fill=SUCCESS, width=0)

            # Info
            info = tk.Frame(part_frame, bg=CARD)
            info.pack(fill="x")
            used_lbl = tk.Label(info, text="Usado: ---", font=FONT_SMALL, fg=TEXT, bg=CARD)
            used_lbl.pack(side="left", padx=(0, 16))
            free_lbl = tk.Label(info, text="Livre: ---", font=FONT_SMALL, fg=TEXT, bg=CARD)
            free_lbl.pack(side="left", padx=(0, 16))
            total_lbl = tk.Label(info, text="Total: ---", font=FONT_SMALL, fg=TEXT, bg=CARD)
            total_lbl.pack(side="left")
            pct_lbl = tk.Label(info, text="---%", font=FONT_SMALL, fg=TEXT_DIM, bg=CARD)
            pct_lbl.pack(side="right")

            self.disk_frames.append({
                "part": part,
                "canvas": canvas,
                "fill_rect": fill_rect,
                "used_lbl": used_lbl,
                "free_lbl": free_lbl,
                "total_lbl": total_lbl,
                "pct_lbl": pct_lbl
            })

    # ========== ABA PINOUT / PORTAS ==========
    def _build_pinout_tab(self):
        container = tk.Frame(self.tab_pinout, bg=CARD)
        container.pack(fill="both", expand=True, padx=24, pady=24)

        # GPIO / Portas
        gpio_frame = tk.LabelFrame(container, text="Status de GPIO / Portas",
                                   font=FONT_HEADER, fg=PRIMARY, bg=CARD, bd=0,
                                   padx=16, pady=12)
        gpio_frame.pack(fill="x", pady=(0, 16))

        # Tabela de portas
        ports_data = [
            ("USB", self._check_usb_ports()),
            ("HDMI", self._check_hdmi()),
            ("Ethernet", "Conectado" if self._is_ethernet_connected() else "Desconectado"),
            ("GPIO", self._check_gpio()),
            ("Câmera USB", self._check_camera()),
        ]

        cols_frame = tk.Frame(gpio_frame, bg=CARD)
        cols_frame.pack(fill="x", pady=6)

        # Header da tabela
        tk.Label(cols_frame, text="Dispositivo", font=FONT_BOLD, fg=TEXT_DIM, bg=CARD, width=20, anchor="w").grid(row=0, column=0, padx=4, pady=4)
        tk.Label(cols_frame, text="Status", font=FONT_BOLD, fg=TEXT_DIM, bg=CARD, width=30, anchor="w").grid(row=0, column=1, padx=4, pady=4)

        for i, (name, status) in enumerate(ports_data):
            status_color = SUCCESS if "ativo" in status.lower() or "conectado" in status.lower() or "dispon" in status.lower() or "detectado" in status.lower() else WARNING
            tk.Label(cols_frame, text=name, font=FONT, fg=TEXT, bg=CARD, width=20, anchor="w").grid(row=i+1, column=0, padx=4, pady=3, sticky="w")
            tk.Label(cols_frame, text=status, font=FONT, fg=status_color, bg=CARD, width=30, anchor="w").grid(row=i+1, column=1, padx=4, pady=3, sticky="w")

        # Tabela de portas de rede (listening)
        net_frame = tk.LabelFrame(container, text="Portas de Rede em Escuta",
                                  font=FONT_HEADER, fg=PRIMARY, bg=CARD, bd=0,
                                  padx=16, pady=12)
        net_frame.pack(fill="both", expand=True)

        port_cols = tk.Frame(net_frame, bg=CARD)
        port_cols.pack(fill="x", pady=6)

        tk.Label(port_cols, text="Protocolo", font=FONT_BOLD, fg=TEXT_DIM, bg=CARD, width=10, anchor="w").grid(row=0, column=0, padx=4, pady=4)
        tk.Label(port_cols, text="Porta", font=FONT_BOLD, fg=TEXT_DIM, bg=CARD, width=8, anchor="w").grid(row=0, column=1, padx=4, pady=4)
        tk.Label(port_cols, text="Endereço", font=FONT_BOLD, fg=TEXT_DIM, bg=CARD, width=20, anchor="w").grid(row=0, column=2, padx=4, pady=4)
        tk.Label(port_cols, text="Processo", font=FONT_BOLD, fg=TEXT_DIM, bg=CARD, width=16, anchor="w").grid(row=0, column=3, padx=4, pady=4)

        self.port_labels = []
        try:
            connections = psutil.net_connections(kind="inet")
            listening = [c for c in connections if c.status == "LISTEN"]
            for i, conn in enumerate(listening[:12]):  # limita a 12
                laddr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "-"
                proto = "TCP" if conn.type == socket.SOCK_STREAM else "UDP"
                pid = conn.pid if conn.pid else "-"
                pname = ""
                if pid != "-":
                    try:
                        pname = psutil.Process(pid).name()
                    except:
                        pname = str(pid)

                tk.Label(port_cols, text=proto, font=FONT_SMALL, fg=TEXT, bg=CARD, width=10, anchor="w").grid(row=i+1, column=0, padx=4, pady=2, sticky="w")
                tk.Label(port_cols, text=str(conn.laddr.port) if conn.laddr else "-", font=FONT_SMALL, fg=TEXT, bg=CARD, width=8, anchor="w").grid(row=i+1, column=1, padx=4, pady=2, sticky="w")
                tk.Label(port_cols, text=laddr, font=FONT_SMALL, fg=TEXT, bg=CARD, width=20, anchor="w").grid(row=i+1, column=2, padx=4, pady=2, sticky="w")
                tk.Label(port_cols, text=pname, font=FONT_SMALL, fg=TEXT_DIM, bg=CARD, width=16, anchor="w").grid(row=i+1, column=3, padx=4, pady=2, sticky="w")
        except (psutil.AccessDenied, PermissionError):
            tk.Label(port_cols, text="Permissão negada para acessar portas.", font=FONT, fg=DANGER, bg=CARD).grid(row=1, column=0, columnspan=4, pady=8)

    # ========== ABA REDE ==========
    def _build_network_tab(self):
        container = tk.Frame(self.tab_network, bg=CARD)
        container.pack(fill="both", expand=True, padx=24, pady=24)

        # Info rede
        net_info_frame = tk.LabelFrame(container, text="Informações de Rede",
                                       font=FONT_HEADER, fg=PRIMARY, bg=CARD, bd=0,
                                       padx=16, pady=12)
        net_info_frame.pack(fill="x", pady=(0, 16))

        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
        except:
            hostname = platform.node()
            ip = "Desconhecido"

        net_info = [
            ("Hostname", hostname),
            ("IP Local", ip),
        ]
        for i, (label, value) in enumerate(net_info):
            tk.Label(net_info_frame, text=f"{label}:", font=FONT_BOLD, fg=TEXT_DIM, bg=CARD).grid(row=i, column=0, sticky="w", pady=3)
            tk.Label(net_info_frame, text=value, font=FONT, fg=TEXT, bg=CARD).grid(row=i, column=1, sticky="w", padx=(12, 0), pady=3)

        # Interfaces de rede
        iface_frame = tk.LabelFrame(container, text="Interfaces de Rede",
                                    font=FONT_HEADER, fg=PRIMARY, bg=CARD, bd=0,
                                    padx=16, pady=12)
        iface_frame.pack(fill="x", pady=(0, 16))

        self.net_iface_labels = []
        self.net_iface_bars = []
        ifaces = psutil.net_if_addrs()
        row = 0
        for iface_name, addrs in ifaces.items():
            if iface_name.startswith("lo") or iface_name.startswith("Loopback"):
                continue
            tk.Label(iface_frame, text=f"{iface_name}", font=FONT_BOLD, fg=TEXT, bg=CARD).grid(row=row, column=0, sticky="w", pady=(8, 2), columnspan=2)
            row += 1
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    tk.Label(iface_frame, text=f"  IP: {addr.address}", font=FONT, fg=TEXT_DIM, bg=CARD).grid(row=row, column=0, sticky="w", padx=(12, 0))
                    tk.Label(iface_frame, text=f"Máscara: {addr.netmask}", font=FONT, fg=TEXT_DIM, bg=CARD).grid(row=row, column=1, sticky="w", padx=(12, 0))
                    row += 1
            row += 1

        # Taxa de transferência
        traffic_frame = tk.LabelFrame(container, text="Tráfego de Rede",
                                      font=FONT_HEADER, fg=PRIMARY, bg=CARD, bd=0,
                                      padx=16, pady=12)
        traffic_frame.pack(fill="x")

        self.net_sent_label = tk.Label(traffic_frame, text="Enviado: ---", font=FONT, fg=TEXT, bg=CARD)
        self.net_sent_label.pack(pady=4)
        self.net_recv_label = tk.Label(traffic_frame, text="Recebido: ---", font=FONT, fg=TEXT, bg=CARD)
        self.net_recv_label.pack(pady=4)

    # ========== ABA SISTEMA ==========
    def _build_system_tab(self):
        container = tk.Frame(self.tab_system, bg=CARD)
        container.pack(fill="both", expand=True, padx=24, pady=24)

        # Informações do SO
        so_frame = tk.LabelFrame(container, text="Sistema Operacional",
                                 font=FONT_HEADER, fg=PRIMARY, bg=CARD, bd=0,
                                 padx=16, pady=12)
        so_frame.pack(fill="x", pady=(0, 16))

        uname = platform.uname()
        boot_time = psutil.boot_time()
        uptime_seconds = time.time() - boot_time
        uptime_str = self._format_uptime(uptime_seconds)

        so_info = [
            ("Sistema", f"{uname.system} {uname.release}"),
            ("Versão", uname.version),
            ("Arquitetura", platform.machine()),
            ("Hostname", uname.node),
            ("Processador", uname.processor or "Desconhecido"),
            ("Tempo de Atividade", uptime_str),
        ]
        for i, (label, value) in enumerate(so_info):
            tk.Label(so_frame, text=f"{label}:", font=FONT_BOLD, fg=TEXT_DIM, bg=CARD).grid(row=i, column=0, sticky="w", pady=3)
            tk.Label(so_frame, text=value, font=FONT, fg=TEXT, bg=CARD).grid(row=i, column=1, sticky="w", padx=(12, 0), pady=3)

        # Processos ativos
        proc_frame = tk.LabelFrame(container, text="Processos em Execução (Top 10 por CPU)",
                                   font=FONT_HEADER, fg=PRIMARY, bg=CARD, bd=0,
                                   padx=16, pady=12)
        proc_frame.pack(fill="both", expand=True)

        self.proc_labels = []
        cols_proc = tk.Frame(proc_frame, bg=CARD)
        cols_proc.pack(fill="x", pady=4)

        tk.Label(cols_proc, text="PID", font=FONT_BOLD, fg=TEXT_DIM, bg=CARD, width=8, anchor="w").grid(row=0, column=0, padx=2, pady=2)
        tk.Label(cols_proc, text="Nome", font=FONT_BOLD, fg=TEXT_DIM, bg=CARD, width=20, anchor="w").grid(row=0, column=1, padx=2, pady=2)
        tk.Label(cols_proc, text="CPU %", font=FONT_BOLD, fg=TEXT_DIM, bg=CARD, width=8, anchor="w").grid(row=0, column=2, padx=2, pady=2)
        tk.Label(cols_proc, text="Memória %", font=FONT_BOLD, fg=TEXT_DIM, bg=CARD, width=10, anchor="w").grid(row=0, column=3, padx=2, pady=2)

        for i in range(1, 11):
            pid_lbl = tk.Label(cols_proc, text="-", font=FONT_SMALL, fg=TEXT_DIM, bg=CARD, width=8, anchor="w")
            pid_lbl.grid(row=i, column=0, padx=2, pady=1, sticky="w")
            name_lbl = tk.Label(cols_proc, text="-", font=FONT_SMALL, fg=TEXT, bg=CARD, width=20, anchor="w")
            name_lbl.grid(row=i, column=1, padx=2, pady=1, sticky="w")
            cpu_lbl = tk.Label(cols_proc, text="-", font=FONT_SMALL, fg=TEXT, bg=CARD, width=8, anchor="w")
            cpu_lbl.grid(row=i, column=2, padx=2, pady=1, sticky="w")
            mem_lbl = tk.Label(cols_proc, text="-", font=FONT_SMALL, fg=TEXT, bg=CARD, width=10, anchor="w")
            mem_lbl.grid(row=i, column=3, padx=2, pady=1, sticky="w")
            self.proc_labels.append((pid_lbl, name_lbl, cpu_lbl, mem_lbl))

    # ========== MÉTODOS AUXILIARES ==========
    def _check_usb_ports(self):
        """Verifica dispositivos USB conectados (Linux/RPi)"""
        count = 0
        try:
            import subprocess
            result = subprocess.run(["lsusb"], capture_output=True, text=True, timeout=3)
            lines = [l for l in result.stdout.strip().split("\n") if l.strip()]
            real_devices = [l for l in lines if "Linux Foundation" not in l and "0000:0000" not in l]
            count = len(real_devices)
        except:
            pass
        if count > 0:
            return f"{count} dispositivo(s) conectado(s)"
        return "Nenhum dispositivo USB detectado"

    def _check_hdmi(self):
        """Verifica saída HDMI no Raspberry Pi"""
        try:
            import subprocess
            result = subprocess.run(["tvservice", "-s"], capture_output=True, text=True, timeout=3)
            if "PAL" in result.stdout or "NTSC" in result.stdout or "HDMI" in result.stdout or "connected" in result.stdout.lower():
                return "HDMI ativo"
            return "HDMI inativo"
        except:
            pass
        try:
            for entry in os.listdir("/sys/class/drm"):
                if "HDMI" in entry or "hdmi" in entry:
                    status_path = f"/sys/class/drm/{entry}/status"
                    if os.path.exists(status_path):
                        with open(status_path) as f:
                            if "connected" in f.read():
                                return "HDMI ativo"
        except:
            pass
        return "HDMI não detectado"

    def _check_gpio(self):
        """Verifica GPIO no Raspberry Pi"""
        try:
            import RPi.GPIO as GPIO
            return "RPi.GPIO disponível"
        except ImportError:
            pass
        try:
            import gpiozero
            return "gpiozero disponível"
        except ImportError:
            pass
        if os.path.exists("/dev/gpiomem"):
            return "GPIO acessível (/dev/gpiomem)"
        return "GPIO não disponível"

    def _check_camera(self):
        """Verifica câmera no Raspberry Pi"""
        try:
            import subprocess
            result = subprocess.run(["libcamera-hello", "--list"], capture_output=True, text=True, timeout=3)
            if result.stdout.strip():
                return "Câmera detectada"
        except:
            pass
        try:
            result = subprocess.run(["raspistill", "-o", "/dev/null", "-t", "1"], capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                return "Câmera detectada"
        except:
            pass
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                cap.release()
                return "Câmera detectada"
            cap.release()
        except ImportError:
            pass
        return "Nenhuma câmera encontrada"

    def _is_ethernet_connected(self):
        """Verifica se a interface de rede está ativa"""
        try:
            addrs = psutil.net_if_stats()
            for name, stats in addrs.items():
                if name.startswith("eth") or name.startswith("en") or "wlan" in name or "Wi-Fi" in name:
                    if stats.isup:
                        return True
            return False
        except:
            return False

    def _format_bytes(self, bytes_val):
        """Formata bytes para unidade legível"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.1f} PB"

    def _format_uptime(self, seconds):
        """Formata tempo de atividade"""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        parts = []
        if days: parts.append(f"{days}d")
        if hours: parts.append(f"{hours}h")
        if minutes: parts.append(f"{minutes}m")
        parts.append(f"{secs}s")
        return " ".join(parts)

    # ========== LOOP DE ATUALIZAÇÃO ==========
    def _update_all(self):
        if not self.running:
            return

        # --- CPU ---
        cpu_pct = psutil.cpu_percent(interval=None)
        color = SUCCESS if cpu_pct < 50 else (WARNING if cpu_pct < 80 else DANGER)
        self.cpu_percent_label.config(text=f"{cpu_pct:.1f}%", fg=color)
        self.cpu_bar_canvas.coords(self.cpu_bar_fill, 0, 0,
                                   self.cpu_bar_canvas.winfo_width() * cpu_pct / 100, 20)
        self.cpu_bar_canvas.itemconfig(self.cpu_bar_fill, fill=color)

        # CPU por núcleo
        try:
            percpu = psutil.cpu_percent(percpu=True)
            for i, val in enumerate(self.percpu_labels):
                if i < len(percpu):
                    val.config(text=f"{percpu[i]:.1f}%")
        except:
            pass

        # --- MEMÓRIA ---
        mem = psutil.virtual_memory()
        ram_pct = mem.percent
        ram_color = SUCCESS if ram_pct < 50 else (WARNING if ram_pct < 80 else DANGER)
        self.ram_percent_label.config(text=f"{ram_pct:.1f}%", fg=ram_color)
        self.ram_bar_canvas.coords(self.ram_bar_fill, 0, 0,
                                   self.ram_bar_canvas.winfo_width() * ram_pct / 100, 20)
        self.ram_bar_canvas.itemconfig(self.ram_bar_fill, fill=ram_color)
        self.ram_used_label.config(text=f"Usado: {self._format_bytes(mem.used)}")
        self.ram_total_label.config(text=f"Total: {self._format_bytes(mem.total)}")
        self.ram_avail_label.config(text=f"Disponível: {self._format_bytes(mem.available)}")

        # SWAP
        swap = psutil.swap_memory()
        swap_pct = swap.percent
        self.swap_percent_label.config(text=f"{swap_pct:.1f}%")
        self.swap_bar_canvas.coords(self.swap_bar_fill, 0, 0,
                                    self.swap_bar_canvas.winfo_width() * swap_pct / 100, 16)
        self.swap_bar_canvas.itemconfig(self.swap_bar_fill, fill=WARNING if swap_pct > 0 else TEXT_DISABLED)
        self.swap_used_label.config(text=f"Usado: {self._format_bytes(swap.used)}")
        self.swap_total_label.config(text=f"Total: {self._format_bytes(swap.total)}")

        # --- DISCO ---
        for df in self.disk_frames:
            try:
                usage = psutil.disk_usage(df["part"].mountpoint)
                pct = usage.percent
                df["canvas"].coords(df["fill_rect"], 0, 0,
                                    df["canvas"].winfo_width() * pct / 100, 16)
                color = SUCCESS if pct < 50 else (WARNING if pct < 80 else DANGER)
                df["canvas"].itemconfig(df["fill_rect"], fill=color)
                df["used_lbl"].config(text=f"Usado: {self._format_bytes(usage.used)}")
                df["free_lbl"].config(text=f"Livre: {self._format_bytes(usage.free)}")
                df["total_lbl"].config(text=f"Total: {self._format_bytes(usage.total)}")
                df["pct_lbl"].config(text=f"{pct:.1f}%")
            except (PermissionError, FileNotFoundError):
                pass

        # --- REDE ---
        try:
            net = psutil.net_io_counters()
            self.net_sent_label.config(text=f"Enviado: {self._format_bytes(net.bytes_sent)}")
            self.net_recv_label.config(text=f"Recebido: {self._format_bytes(net.bytes_recv)}")
        except:
            pass

        # --- SISTEMA (Processos) ---
        try:
            processes = sorted(psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]),
                               key=lambda p: p.info.get("cpu_percent") or 0, reverse=True)[:10]
            for i, (pid_lbl, name_lbl, cpu_lbl, mem_lbl) in enumerate(self.proc_labels):
                if i < len(processes):
                    p = processes[i]
                    pid_lbl.config(text=str(p.info["pid"]))
                    name_lbl.config(text=p.info["name"][:18] if p.info["name"] else "-")
                    cpu_lbl.config(text=f"{p.info.get('cpu_percent', 0) or 0:.1f}%")
                    mem_lbl.config(text=f"{p.info.get('memory_percent', 0) or 0:.1f}%")
                else:
                    pid_lbl.config(text="-")
                    name_lbl.config(text="-")
                    cpu_lbl.config(text="-")
                    mem_lbl.config(text="-")
        except:
            pass

        # Próxima atualização em 2 segundos
        self.app.frame.after(2000, self._update_all)

    def cleanup(self):
        """Método chamado ao sair da tela"""
        self.running = False
