"""Placeholder da gestão de usuários."""

from components import ui
from views.base_page import Page


class UsersPage(Page):
    route = "users"

    def build(self):
        body = ui.frame(self, "bg")
        body.pack(fill="both", expand=True, padx=20, pady=12)

        ui.label(body, "USUÁRIOS", kind="title").pack(anchor="w")
        ui.label(
            body, "Cadastro e permissões de operadores da linha.", kind="small"
        ).pack(anchor="w", pady=(0, 12))

        panel = ui.panel(body, title="Em breve", pack=False)
        panel.pack(fill="x")
        self.text = ui.label(
            panel.content,
            "A gestão de usuários ainda não está habilitada.\n\n"
            "Enquanto isso, as credenciais podem ser definidas pelas variáveis "
            "SPIS_ADMIN_USER e SPIS_ADMIN_PASSWORD.",
            kind="body",
            justify="left",
        )
        self.text.pack(anchor="w")

    def on_show(self):
        self.app.refresh_header_stats()
        user = self.app.current_user or "visitante"
        self.text.configure(
            text=(
                f"Usuário atual: {user}\n\n"
                "A gestão de usuários ainda não está habilitada.\n\n"
                "Enquanto isso, as credenciais podem ser definidas pelas variáveis "
                "SPIS_ADMIN_USER e SPIS_ADMIN_PASSWORD."
            )
        )
