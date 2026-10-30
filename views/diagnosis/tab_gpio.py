"""Aba GPIO - Mostra status REAL de todos os 40 pinos via pinctrl"""
import tkinter as tk
from components import ui
from styles.theme import *
from processes.gpio_checker import GpioChecker
import platform_support
from .base_tab import BaseTab

# Layout do conector J8 (GPIO 40 pinos) do RPi 4
# Cada tupla: (pino_fisico_esq, bcm_esq, pino_fisico_dir, bcm_dir)
LAYOUT = [
    (1, None, 2, None),      # 3.3V | 5V
    (3, 2, 5, 3),            # GPIO2 | GPIO3
    (7, 4, 8, 14),           # GPIO4 | GPIO14
    (9, None, 10, 15),       # GND | GPIO15
    (11, 17, 12, 18),        # GPIO17 | GPIO18
    (13, 27, 14, None),      # GPIO27 | GND
    (15, 22, 16, 23),        # GPIO22 | GPIO23
    (17, None, 18, 24),      # 3.3V | GPIO24
    (19, 10, 20, None),      # GPIO10 | GND
    (21, 9, 22, 25),         # GPIO9 | GPIO25
    (23, 11, 24, 8),         # GPIO11 | GPIO8
    (25, None, 26, 7),       # GND | GPIO7
    (27, 0, 28, 1),          # GPIO0 | GPIO1
    (29, 5, 30, None),       # GPIO5 | GND
    (31, 6, 32, 12),         # GPIO6 | GPIO12
    (33, 13, 34, None),      # GPIO13 | GND
    (35, 19, 36, 16),        # GPIO19 | GPIO16
    (37, 26, 38, 20),        # GPIO26 | GPIO20
    (39, None, 40, 21),      # GND | GPIO21
]

# Mapeamento reverso: bcm -> pino_fisico
BCM_TO_PIN = {}
for (p_esq, bcm_esq, p_dir, bcm_dir) in LAYOUT:
    if bcm_esq is not None:
        BCM_TO_PIN[bcm_esq] = p_esq
    if bcm_dir is not None:
        BCM_TO_PIN[bcm_dir] = p_dir

# Nomes especiais para pinos sem GPIO
PIN_NAMES = {
    1: "3.3V", 2: "5V",
    4: "5V", 6: "GND",
    9: "GND", 14: "GND",
    17: "3.3V", 20: "GND",
    25: "GND", 30: "GND",
    34: "GND", 39: "GND",
}

# Modos especiais (sem GPIO)
PIN_MODES = {
    1: "PWR", 2: "PWR",
    4: "PWR", 6: "GND",
    9: "GND", 14: "GND",
    17: "PWR", 20: "GND",
    25: "GND", 30: "GND",
    34: "GND", 39: "GND",
}


class GpioTab(BaseTab):
    def __init__(self, parent):
        super().__init__(parent)

        # Scroll
        cv, sf = ui.scrollable(self.container, bg=CARD)
        cv.pack(fill="both", expand=True)

        # Título
        title = tk.Label(sf, text="GPIO Pinout - Status em Tempo Real", 
                        font=FONT_TITLE, fg=PRIMARY, bg=CARD)
        title.pack(anchor="w", padx=16, pady=(16,8))

        if not platform_support.io_hardware_supported():
            ui.label(
                sf,
                "GPIO físico disponível apenas no Raspberry Pi. "
                f"Plataforma atual: {platform_support.system_label()}.",
                kind="small",
                bg=CARD,
            ).pack(anchor="w", padx=16, pady=(0, 8))

        # Frame para os pinos
        pins_frame = ui.frame(sf, "card")
        pins_frame.pack(fill="both", expand=True, padx=16, pady=8)

        self.pin_widgets = {}  # {pino_fisico: {side: "left"/"right", label_widgets}}

        # Cabeçalho (2 conjuntos: esquerda e direita)
        header_frame = ui.frame(pins_frame, "card")
        header_frame.pack(fill="x", pady=(0,8))

        # Cabeçalho lado esquerdo
        left_header = ui.frame(header_frame, "card")
        left_header.pack(side="left", fill="x", expand=True)
        tk.Label(left_header, text="Pino", font=FONT_BOLD, fg=TEXT_DIM, bg=CARD, width=5).pack(side="left", padx=2)
        tk.Label(left_header, text="BCM", font=FONT_BOLD, fg=TEXT_DIM, bg=CARD, width=5).pack(side="left", padx=2)
        tk.Label(left_header, text="Nome", font=FONT_BOLD, fg=TEXT_DIM, bg=CARD, width=8).pack(side="left", padx=2)
        tk.Label(left_header, text="Modo", font=FONT_BOLD, fg=TEXT_DIM, bg=CARD, width=6).pack(side="left", padx=2)
        tk.Label(left_header, text="Pull", font=FONT_BOLD, fg=TEXT_DIM, bg=CARD, width=4).pack(side="left", padx=2)
        tk.Label(left_header, text="Val", font=FONT_BOLD, fg=TEXT_DIM, bg=CARD, width=4).pack(side="left", padx=2)

        # Espaço entre os lados
        tk.Label(header_frame, text="  ", bg=CARD).pack(side="left")

        # Cabeçalho lado direito
        right_header = ui.frame(header_frame, "card")
        right_header.pack(side="left", fill="x", expand=True)
        tk.Label(right_header, text="Pino", font=FONT_BOLD, fg=TEXT_DIM, bg=CARD, width=5).pack(side="left", padx=2)
        tk.Label(right_header, text="BCM", font=FONT_BOLD, fg=TEXT_DIM, bg=CARD, width=5).pack(side="left", padx=2)
        tk.Label(right_header, text="Nome", font=FONT_BOLD, fg=TEXT_DIM, bg=CARD, width=8).pack(side="left", padx=2)
        tk.Label(right_header, text="Modo", font=FONT_BOLD, fg=TEXT_DIM, bg=CARD, width=6).pack(side="left", padx=2)
        tk.Label(right_header, text="Pull", font=FONT_BOLD, fg=TEXT_DIM, bg=CARD, width=4).pack(side="left", padx=2)
        tk.Label(right_header, text="Val", font=FONT_BOLD, fg=TEXT_DIM, bg=CARD, width=4).pack(side="left", padx=2)

        # Cria linha para cada par de pinos do LAYOUT
        for (p_esq, bcm_esq, p_dir, bcm_dir) in LAYOUT:
            row_frame = tk.Frame(pins_frame, bg=CARD, relief="flat", bd=0)
            row_frame.pack(fill="x", pady=2)

            # --- Lado esquerdo ---
            pin_esq_frame = ui.frame(row_frame, "card")
            pin_esq_frame.pack(side="left", fill="x", expand=True)

            widgets_esq = self._create_pin_widgets(pin_esq_frame, p_esq, bcm_esq)
            self.pin_widgets[p_esq] = {"side": "left", **widgets_esq}

            # Espaço entre os lados
            tk.Label(row_frame, text="  ", bg=CARD).pack(side="left")

            # --- Lado direito ---
            pin_dir_frame = ui.frame(row_frame, "card")
            pin_dir_frame.pack(side="left", fill="x", expand=True)

            widgets_dir = self._create_pin_widgets(pin_dir_frame, p_dir, bcm_dir)
            self.pin_widgets[p_dir] = {"side": "right", **widgets_dir}

        # Legenda
        leg_frame = ui.frame(sf, "card")
        leg_frame.pack(anchor="w", padx=16, pady=(16,8))
        
        tk.Label(leg_frame, text="Modo: ", font=FONT_BOLD, fg=TEXT_DIM, bg=CARD).pack(side="left")
        for mode, color in [("ip", "#4CAF50"), ("op", "#2196F3"), ("a0-a5", "#FF9800"), ("PWR/GND", "#6B7280")]:
            tk.Label(leg_frame, text="■", fg=color, bg=CARD, font=FONT_SMALL).pack(side="left", padx=(8,2))
            tk.Label(leg_frame, text=mode, font=FONT_SMALL, fg=TEXT_DIM, bg=CARD).pack(side="left", padx=(0,6))

    def _create_pin_widgets(self, parent, pino_fisico, bcm):
        """Cria os widgets para um pino (esquerda ou direita)"""
        nome = PIN_NAMES.get(pino_fisico, f"GPIO{bcm}" if bcm is not None else "---")
        bcm_text = str(bcm) if bcm is not None else "--"

        widgets = {
            "pino": tk.Label(parent, text=str(pino_fisico), font=FONT, fg=TEXT_DIM, bg=CARD, width=5, anchor="e"),
            "bcm": tk.Label(parent, text=bcm_text, font=FONT, fg=TEXT_DIM, bg=CARD, width=5, anchor="e"),
            "nome": tk.Label(parent, text=nome, font=FONT, fg=TEXT, bg=CARD, width=8, anchor="w"),
            "modo": tk.Label(parent, text="--", font=FONT, fg=TEXT_DIM, bg=CARD, width=6, anchor="c"),
            "pull": tk.Label(parent, text="--", font=FONT, fg=TEXT_DIM, bg=CARD, width=4, anchor="c"),
            "val": tk.Label(parent, text="--", font=FONT_BOLD, fg=TEXT, bg=CARD, width=4, anchor="c"),
        }

        for w in widgets.values():
            w.pack(side="left", padx=2)

        return widgets

    def update(self):
        """Atualiza status real de todos os pinos"""
        pinos = GpioChecker.pinctrl_status()

        # Mapear modos para cores
        mode_colors = {
            "ip": "#4CAF50",  # input - verde
            "op": "#2196F3",  # output - azul
            "a0": "#FF9800",  # alt0 - laranja
            "a1": "#FF9800",  # alt1
            "a2": "#FF9800",  # alt2
            "a3": "#FF9800",  # alt3
            "a4": "#FF9800",  # alt4
            "a5": "#FF9800",  # alt5
        }

        # Mapear pull para símbolo
        pull_map = {
            "pu": "↑",   # pull-up
            "pd": "↓",   # pull-down
            "pn": "-",   # none
        }

        # Mapear valores
        value_colors = {
            "hi": "#4CAF50",  # verde
            "lo": "#1a3a1a",  # verde escuro
        }

        for (p_esq, bcm_esq, p_dir, bcm_dir) in LAYOUT:
            # Atualiza lado esquerdo
            self._update_pin_widget(p_esq, bcm_esq, pinos, mode_colors, pull_map, value_colors)
            # Atualiza lado direito
            self._update_pin_widget(p_dir, bcm_dir, pinos, mode_colors, pull_map, value_colors)

    def _update_pin_widget(self, pino_fisico, bcm, pinos_status, mode_colors, pull_map, value_colors):
        """Atualiza widgets de um único pino"""
        w = self.pin_widgets[pino_fisico]

        # Define nome
        nome = PIN_NAMES.get(pino_fisico, f"GPIO{bcm}" if bcm is not None else "---")
        w["nome"].configure(text=nome)

        # Se não tem BCM (pinos de alimentação/GND)
        if bcm is None:
            modo_especial = PIN_MODES.get(pino_fisico, "---")
            w["modo"].configure(text=modo_especial, fg="#6B7280")
            w["pull"].configure(text="--", fg=TEXT_DIM)
            w["val"].configure(text="--", fg=TEXT_DIM)
            w["pino"].configure(fg=TEXT_DIM)
            w["bcm"].configure(text="--", fg=TEXT_DIM)
            return

        # Pino com GPIO
        w["bcm"].configure(text=str(bcm), fg=TEXT_DIM)
        w["pino"].configure(fg=TEXT_DIM)

        if bcm in pinos_status:
            info = pinos_status[bcm]
            mode = info["mode"]
            pull = info["pull"]
            value = info["value"]
            function = info["function"]

            # Atualiza widgets
            w["nome"].configure(
                text=function.split()[0] if function else f"GPIO{bcm}", fg=TEXT
            )
            
            mode_color = mode_colors.get(mode, TEXT_DIM)
            w["modo"].configure(text=mode, fg=mode_color)
            
            pull_symbol = pull_map.get(pull, pull)
            w["pull"].configure(text=pull_symbol, fg=TEXT_DIM)
            
            value_color = value_colors.get(value, TEXT_DIM)
            w["val"].configure(text=value.upper(), fg=value_color)
        else:
            # Sem dados - pino não configurado/exportado
            w["nome"].configure(text=f"GPIO{bcm}", fg=TEXT_DIM)
            w["modo"].configure(text="--", fg=TEXT_DIM)
            w["pull"].configure(text="--", fg=TEXT_DIM)
            w["val"].configure(text="--", fg=TEXT_DIM)
