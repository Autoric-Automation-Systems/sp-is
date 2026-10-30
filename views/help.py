"""Página de Ajuda com o passo a passo de operação."""

from components import ui
from styles.theme import *
from views.base_page import Page

SECTIONS = (
    (
        "1. Preparar a receita",
        [
            "A receita em uso fica no topo da janela (header) e vale em todas as telas.",
            "Abra Receitas e clique em Nova receita (é necessário estar logado).",
            "Digite o nome e ajuste os três ROIs (Tampa, Nível e ROI 3) com o mouse ou com os campos X/Y.",
            "Cada ROI tem nome editável e uma janela de acerto em % da imagem de referência.",
            "Salve. A receita passa a ser a receita em uso automaticamente.",
        ],
    ),
    (
        "2. Executar a inspeção",
        [
            "Na tela Principal, confirme a receita em uso.",
            "Clique em EXECUTAR CICLO ou acione o trigger por pino, se houver.",
            "O resultado e o % de cada ROI aparecem no painel da última captura e no histórico.",
        ],
    ),
    (
        "3. Interpretar os resultados",
        [
            "OK: todos os ROIs ficaram dentro da janela de acerto.",
            "ERRO: <ROI>: o % de acerto do ROI citado ficou fora da janela. Se mais de um falhar, todos aparecem (ex.: ERRO: NÍVEL + RÓTULO).",
            "O expulsor é acionado em qualquer reprovação; o texto do resultado usa a cor do ROI reprovado.",
            "SEM REFERÊNCIA / ROI INVÁLIDO / CÂMERA INDISPONÍVEL: erro de processo, sem acionar o expulsor.",
            "O % de acerto compara a região com a imagem de referência salva na receita (quanto maior, mais parecida).",
        ],
    ),
    (
        "4. Ajustar a janela de acerto",
        [
            "Abra a receita e use 'Capturar referência' para congelar a imagem de comparação.",
            "O campo 'Agora' mostra o % de acerto ao vivo de cada ROI.",
            "Defina mínimo e máximo (ex.: 85 a 100%) e use os botões − / + para ajuste fino.",
        ],
    ),
    (
        "5. Verificar o hardware",
        [
            "Diagnósticos → Sensores / Saídas mostra o estado das entradas e permite testar o expulsor e o LED.",
            "As abas CPU, Memória, Disco, Rede e Sistema funcionam em qualquer plataforma;",
            "GPIO, sensores da placa e câmera CSI exigem Raspberry Pi (no PC o I/O é simulado).",
        ],
    ),
)

SHORTCUTS = (
    ("Clique em uma miniatura", "Reabre a captura e seus detalhes"),
    ("Voltar ao vivo", "Retorna a imagem da câmera na tela Principal"),
    ("Estatísticas", "Abre o detalhamento por resultado e por receita"),
    ("Sair", "Encerra a sessão e volta ao modo visitante"),
)


class HelpPage(Page):
    route = "help"

    def build(self):
        container, inner = ui.scrollable(self, bg=BG)
        container.pack(fill="both", expand=True)

        body = ui.frame(inner, "bg")
        body.pack(fill="both", expand=True, padx=20, pady=16)

        ui.label(body, "AJUDA", kind="title").pack(anchor="w")
        ui.label(
            body,
            "Passo a passo para operar a inspeção e ajustar o sistema.",
            kind="small",
        ).pack(anchor="w", pady=(0, 12))

        for title, items in SECTIONS:
            panel = ui.panel(body, title=title, pack=False)
            panel.pack(fill="x", pady=(0, 10))
            for item in items:
                row = ui.frame(panel.content, "card")
                row.pack(fill="x", pady=1)
                ui.label(row, "•", kind="accent", bg=CARD).pack(side="left", padx=(0, 8))
                ui.paragraph(row, item, padding=48).pack(
                    side="left", fill="x", expand=True
                )

        panel = ui.panel(body, title="Atalhos da interface", pack=False)
        panel.pack(fill="x", pady=(0, 10))
        grid = ui.frame(panel.content, "card")
        grid.pack(fill="x")
        for row_index, (action, description) in enumerate(SHORTCUTS):
            ui.label(grid, action, kind="bold", bg=CARD).grid(
                row=row_index, column=0, sticky="w", pady=2
            )
            ui.paragraph(grid, description, kind="small", padding=180).grid(
                row=row_index, column=1, sticky="we", padx=(16, 0), pady=2
            )
        grid.grid_columnconfigure(1, weight=1)

    def on_show(self):
        self.app.refresh_header_stats()
