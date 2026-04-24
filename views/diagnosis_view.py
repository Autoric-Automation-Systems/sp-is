"""View principal de Diagnóstico - Orquestra as abas"""
import tkinter as tk
from tkinter import ttk
from components.layout import BaseLayout
from styles.theme import *

# Importa as abas da subpasta views/diagnosis/
from views.diagnosis.tab_cpu import CpuTab
from views.diagnosis.tab_mem import MemTab
from views.diagnosis.tab_disk import DiskTab
from views.diagnosis.tab_gpio import GpioTab
from views.diagnosis.tab_network import NetworkTab
from views.diagnosis.tab_system import SystemTab


class DiagnosisView:
    def __init__(self, parent, app):
        self.app = app
        layout = BaseLayout(parent, app)
        layout.content.configure(bg=BG)

        # -------- HEADER --------
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
        style.configure("TNotebook", background=BG, borderwidth=0, padding=0)
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
        style.configure("TFrame", background=CARD)

        notebook = ttk.Notebook(layout.content, style="TNotebook")
        notebook.pack(fill="both", expand=True, padx=32, pady=20)

        # -------- CRIA AS ABAS --------
        tab_cpu = ttk.Frame(notebook)
        tab_mem = ttk.Frame(notebook)
        tab_disk = ttk.Frame(notebook)
        tab_gpio = ttk.Frame(notebook)
        tab_network = ttk.Frame(notebook)
        tab_system = ttk.Frame(notebook)

        notebook.add(tab_cpu, text="CPU")
        notebook.add(tab_mem, text="Memória")
        notebook.add(tab_disk, text="HD / Disco")
        notebook.add(tab_gpio, text="GPIO / Portas")
        notebook.add(tab_network, text="Rede")
        notebook.add(tab_system, text="Sistema")

        # -------- INSTANCIA OS CONTROLADORES DE CADA ABA --------
        self.cpu = CpuTab(tab_cpu)
        self.mem = MemTab(tab_mem)
        self.disk = DiskTab(tab_disk)
        self.gpio = GpioTab(tab_gpio)
        self.network = NetworkTab(tab_network)
        self.system = SystemTab(tab_system)

        # -------- LOOP DE ATUALIZAÇÃO --------
        self.running = True
        self._after_id = None
        self._update_all()

    def _update_all(self):
        if not self.running:
            return
        try:
            self.cpu.update()
        except Exception as e:
            print(f"Erro ao atualizar CPU: {e}")
        try:
            self.mem.update()
        except Exception as e:
            print(f"Erro ao atualizar Memória: {e}")
        try:
            self.disk.update()
        except Exception as e:
            print(f"Erro ao atualizar Disco: {e}")
        try:
            self.gpio.update()
        except Exception as e:
            print(f"Erro ao atualizar GPIO: {e}")
        try:
            self.network.update()
        except Exception as e:
            print(f"Erro ao atualizar Rede: {e}")
        try:
            self.system.update()
        except Exception as e:
            print(f"Erro ao atualizar Sistema: {e}")
        try:
            self._after_id = self.app.after(2000, self._update_all)
        except Exception as e:
            print(f"Erro ao agendar próxima atualização: {e}")

    def cleanup(self):
        self.running = False
        if self._after_id is not None:
            try:
                self.app.after_cancel(self._after_id)
            except:
                pass

    # Cancel any pending "after" callbacks when destroyed
    def destroy(self):
        self.running = False
        if self._after_id:
            try:
                self.app.after_cancel(self._after_id)
            except:
                pass

