"""Página Sobre com a descrição do aplicativo."""
import sys

import cv2

import platform_support
from components import ui
from paths import BASE_DIR
from styles.theme import *
from views.base_page import Page

VERSION = "1.1.0"


class AboutPage(Page):
    route = "about"

    def build(self):
        container, inner = ui.scrollable(self, bg=BG)
        container.pack(fill="both", expand=True)

        body = ui.frame(inner, "bg")
        body.pack(fill="both", expand=True, padx=20, pady=16)

        ui.label(body, "SOBRE", kind="title").pack(anchor="w")
        ui.label(body, f"SP-IS · Smart Plant Inspection System · versão {VERSION}", kind="small").pack(
            anchor="w", pady=(0, 12)
        )

        panel = ui.panel(body, title="O que é", pack=False)
        panel.pack(fill="x", pady=(0, 10))
        ui.paragraph(
            panel.content,
            "O SP-IS é uma estação de inspeção visual para linhas de envase. Ele compara a "
            "região de interesse (ROI) da tampa de cada garrafa ou pote com o padrão cadastrado "
            "na receita e decide, em milissegundos, se a peça está aprovada.\n\n"
            "A decisão usa a densidade de bordas (algoritmo Canny) e o brilho médio da região: "
            "a tampa lisa e clara gera poucas bordas, enquanto o bocal aberto (roscas) gera "
            "muitas. Quando a peça é reprovada, o expulsor é acionado pelo tempo configurado.",
        ).pack(fill="x")

        panel = ui.panel(body, title="Recursos", pack=False)
        panel.pack(fill="x", pady=(0, 10))
        for item in (
            "Cadastro de receitas por ROI com captura da imagem de referência.",
            "Trigger pelo botão da tela e por entrada digital (BCM).",
            "Expulsor com tempo de pulso configurável e LED de trigger.",
            "Histórico das últimas capturas, com imagem e resultado.",
            "Estatísticas em tempo real por resultado e por receita, persistidas em SQL.",
            "Diagnóstico de CPU, memória, disco, rede, GPIO, sensores e saídas.",
        ):
            row = ui.frame(panel.content, "card")
            row.pack(fill="x", pady=1)
            ui.label(row, "•", kind="accent", bg=CARD).pack(side="left", padx=(0, 8))
            ui.label(row, item, kind="body", bg=CARD).pack(side="left")

        panel = ui.panel(body, title="Ambiente", pack=False)
        panel.pack(fill="x", pady=(0, 10))
        info = ui.frame(panel.content, "card")
        info.pack(fill="x")
        rows = [
            ("Sistema", platform_support.system_label()),
            ("Python", sys.version.split()[0]),
            ("OpenCV", cv2.__version__),
            (
                "Hardware",
                "Raspberry Pi (GPIO + câmera CSI)"
                if platform_support.is_raspberry_pi()
                else "PC (webcam USB e I/O simulado)",
            ),
            ("Diretório", str(BASE_DIR)),
        ]
        for index, (key, value) in enumerate(rows):
            ui.label(info, key, kind="small", bg=CARD).grid(
                row=index, column=0, sticky="w", pady=1
            )
            ui.label(info, value, kind="body", bg=CARD).grid(
                row=index, column=1, sticky="w", padx=(16, 0), pady=1
            )

        panel = ui.panel(body, title="Desenvolvimento", pack=False)
        panel.pack(fill="x", pady=(0, 10))
        ui.paragraph(
            panel.content,
            "Desenvolvido por Autoric Automação e Sistemas.\nwww.autoric.com.br",
        ).pack(fill="x")

    def on_show(self):
        self.app.refresh_header_stats()
