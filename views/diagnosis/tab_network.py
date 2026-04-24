"""Aba de Rede"""
import tkinter as tk
import socket
from styles.theme import *
from processes.monitor import SystemMonitor
from .base_tab import BaseTab


class NetworkTab(BaseTab):
    def __init__(self, parent):
        super().__init__(parent)

        info_frame = self._make_label_frame(self.container, "Informações de Rede")
        hostname, ip = SystemMonitor.hostname_ip()
        self._make_info_table(info_frame, [
            ("Hostname", hostname),
            ("IP Local", ip),
        ])

        iface_frame = self._make_label_frame(self.container, "Interfaces de Rede")
        addrs, _ = SystemMonitor.net_ifaces()
        row = 0
        for name, addr_list in addrs.items():
            if name.startswith("lo"):
                continue
            tk.Label(iface_frame, text=name, font=FONT_BOLD, fg=TEXT, bg=CARD).grid(
                row=row, column=0, sticky="w", pady=(8, 2), columnspan=2)
            row += 1
            for a in addr_list:
                if a.family == socket.AF_INET:
                    tk.Label(iface_frame, text=f"  IP: {a.address}", font=FONT, fg=TEXT_DIM, bg=CARD).grid(
                        row=row, column=0, sticky="w", padx=(12, 0))
                    tk.Label(iface_frame, text=f"Máscara: {a.netmask}", font=FONT, fg=TEXT_DIM, bg=CARD).grid(
                        row=row, column=1, sticky="w", padx=(12, 0))
                    row += 1
            row += 1

        traffic = self._make_label_frame(self.container, "Tráfego de Rede")
        self.sent_lbl = tk.Label(traffic, text="Enviado: ---", font=FONT, fg=TEXT, bg=CARD)
        self.sent_lbl.pack(pady=4)
        self.recv_lbl = tk.Label(traffic, text="Recebido: ---", font=FONT, fg=TEXT, bg=CARD)
        self.recv_lbl.pack(pady=4)

    def update(self):
        net = SystemMonitor.net_io()
        fmt = SystemMonitor.format_bytes
        self.sent_lbl.config(text=f"Enviado: {fmt(net.bytes_sent)}")
        self.recv_lbl.config(text=f"Recebido: {fmt(net.bytes_recv)}")
