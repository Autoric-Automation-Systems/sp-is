"""View principal de Diagnóstico - orquestra as abas."""
import logging

import customtkinter as ctk

from components import ui
from styles.theme import *
from views.base_page import Page
from views.diagnosis.tab_cpu import CpuTab
from views.diagnosis.tab_disk import DiskTab
from views.diagnosis.tab_gpio import GpioTab
from views.diagnosis.tab_io import IoTab
from views.diagnosis.tab_mem import MemTab
from views.diagnosis.tab_network import NetworkTab
from views.diagnosis.tab_system import SystemTab

LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL_MS = 1000

TAB_CLASSES = {
    "io": IoTab,
    "cpu": CpuTab,
    "mem": MemTab,
    "disk": DiskTab,
    "gpio": GpioTab,
    "network": NetworkTab,
    "system": SystemTab,
}

TAB_LABELS = {
    "Sensores / Saídas": "io",
    "CPU": "cpu",
    "Memória": "mem",
    "HD / Disco": "disk",
    "GPIO / Portas": "gpio",
    "Rede": "network",
    "Sistema": "system",
}


class DiagnosisPage(Page):
    route = "diagnosis"

    def build(self):
        self._after_id = None

        header_frame = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        header_frame.pack(fill="x", padx=24, pady=(14, 0))

        ui.label(header_frame, "DIAGNÓSTICO DO SISTEMA", kind="title", bg=BG).pack(
            anchor="w"
        )
        ui.label(
            header_frame,
            "Monitoramento de hardware, sistema e rede da máquina",
            kind="small",
            bg=BG,
        ).pack(anchor="w", pady=(2, 0))

        self.tabview = ctk.CTkTabview(
            self,
            fg_color=BG,
            corner_radius=8,
            segmented_button_fg_color=BUTTON_BG,
            segmented_button_selected_color=CARD,
            segmented_button_selected_hover_color=BUTTON_HOVER,
            segmented_button_unselected_color=BUTTON_BG,
            segmented_button_unselected_hover_color=BUTTON_HOVER,
            text_color=TEXT,
            segmented_button_font=ui.font("Segoe UI", 12, "bold"),
        )
        self.tabview.pack(fill="both", expand=True, padx=24, pady=(12, 16))

        self.tabs = {}
        self._tab_order = list(TAB_CLASSES)
        for label, key in TAB_LABELS.items():
            frame = self.tabview.add(label)
            self.tabs[key] = TAB_CLASSES[key](frame)

    def _update_all(self):
        try:
            if not self.running or not self.app.winfo_exists():
                return
        except Exception:
            self.running = False
            return

        key = TAB_LABELS.get(self.tabview.get(), "cpu")
        try:
            self.tabs[key].update()
        except Exception:
            LOGGER.exception("Erro ao atualizar a aba %s", key)

        try:
            self._after_id = self.app.after(UPDATE_INTERVAL_MS, self._update_all)
        except Exception:
            self.running = False

    def on_show(self):
        self.app.refresh_header_stats()
        self.running = True
        if self._after_id is not None:
            try:
                self.app.after_cancel(self._after_id)
            except Exception:
                pass
        self._after_id = None
        self._update_all()

    def on_hide(self):
        self.running = False
        if self._after_id is not None:
            try:
                self.app.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None
