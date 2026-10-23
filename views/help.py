"""Página de Ajuda com o passo a passo de operação."""

from components import ui
from styles.theme import *
from views.base_page import Page

SECTIONS = (
    (
        "1. Preparar a receita",
        [
            "Abra Receitas e clique em Nova receita (é necessário estar logado).",
            "Digite o nome, posicione a peça na esteira e desenhe o ROI sobre a região da tampa.",
            "Salve. A receita passa a ser a receita em uso na tela Principal.",
        ],
    ),
    (
        "2. Executar a inspeção",
        [
            "Na tela Principal, confirme a receita em uso.",
            "Clique em EXECUTAR CICLO ou acione o trigger por pino, se houver.",
            "O resultado aparece no painel da última captura e é salvo no histórico.",
        ],
    ),
    (
        "3. Interpretar os resultados",
        [
            "OK: peça aprovada.",
            "ERRO: SEM TAMPA: muitas bordas no ROI — o expulsor é acionado.",
            "SEM GARRAFA: brilho médio abaixo do mínimo configurado.",
            "ROI INVÁLIDO / CÂMERA INDISPONÍVEL: erro de processo, sem acionar o expulsor.",
        ],
    ),
    (
        "4. Ajustar a sensibilidade",
        [
            "Em Configurações, ajuste Threshold (pixels de borda) e Brilho mínimo.",
            "Valores maiores de threshold tornam a detecção de tampa mais tolerante.",
        ],
    ),
    (
        "5. Verificar o hardware",
        [
            "Diagnósticos → Sensores / Saídas mostra o estado das entradas e permite testar o expulsor e o LED.",
            "As abas CPU, Memória, Disco, GPIO, Rede e Sistema ajudam a diagnosticar o Raspberry Pi.",
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
