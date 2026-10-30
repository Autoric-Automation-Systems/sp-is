from tkinter import messagebox

from components import ui
from services.recipe_service import delete_recipe, list_recipes
from styles.theme import *
from views.base_page import Page


class RecipesPage(Page):
    route = "recipes"

    def build(self):
        self.recipes = []

        body = ui.frame(self, "bg")
        body.pack(fill="both", expand=True, padx=20, pady=12)

        header = ui.frame(body, "bg")
        header.pack(fill="x", pady=(0, 10))
        ui.label(header, "RECEITAS", kind="title").pack(side="left")
        ui.label(
            header,
            "A receita em uso é escolhida no topo da janela e vale para todas as telas.",
            kind="small",
        ).pack(side="left", padx=(12, 0), pady=(8, 0))
        ui.button(
            header, "Nova receita", command=self.new_recipe, variant="primary"
        ).pack(side="right")

        self.list_panel = ui.panel(body, title="Receitas cadastradas", pack=False)
        self.list_panel.pack(fill="both", expand=True)
        self.list_frame = self.list_panel.content

    # ------------------------------------------------------------------ dados
    def on_show(self):
        self.app.refresh_header_stats()
        self.load_recipes()

    def load_recipes(self):
        self.recipes = list_recipes()

        active = self.app.current_recipe
        active_name = active["name"] if active else ""

        for child in self.list_frame.winfo_children():
            child.destroy()

        head = ui.frame(self.list_frame, "header")
        head.pack(fill="x")
        ui.label(head, "Nome", kind="small", bg=HEADER_BG).pack(
            side="left", fill="x", expand=True, padx=12, pady=7
        )
        ui.label(head, "Atualizada em", kind="small", bg=HEADER_BG, width=18, anchor="w").pack(
            side="left", padx=8
        )
        ui.label(head, "Ações", kind="small", bg=HEADER_BG).pack(side="right", padx=18)

        if not self.recipes:
            ui.label(self.list_frame, "Nenhuma receita cadastrada.", kind="muted").pack(
                anchor="w", pady=16, padx=12
            )
            return

        for index, recipe in enumerate(self.recipes):
            bg = CARD if index % 2 == 0 else BG
            row = ui.frame(self.list_frame, bg)
            row.pack(fill="x", pady=1)

            name_frame = ui.frame(row, bg)
            name_frame.pack(side="left", fill="x", expand=True, padx=12, pady=7)
            ui.label(name_frame, recipe["name"], kind="bold", bg=bg).pack(side="left")
            if recipe["name"] == active_name:
                ui.badge(name_frame, "EM USO", PRIMARY).pack(side="left", padx=(8, 0))
            rois = recipe.get("rois") or []
            if rois:
                ui.label(
                    name_frame,
                    " · ".join(
                        f"{item['name']} {item['min_match']:g}–{item['max_match']:g}%"
                        for item in rois
                    ),
                    kind="small",
                    bg=bg,
                ).pack(side="left", padx=(10, 0))

            updated = recipe.get("updated_at") or recipe.get("created_at") or "—"
            ui.label(row, str(updated), kind="small", bg=bg, width=18, anchor="w").pack(
                side="left", padx=8
            )

            actions = ui.frame(row, bg)
            actions.pack(side="right", padx=10)
            if recipe["name"] != active_name:
                ui.button(
                    actions, "Usar", command=lambda r=recipe: self.use(r),
                    variant="primary", size="sm", width=7,
                ).pack(side="left", padx=2)
            ui.button(
                actions, "Editar", command=lambda r=recipe: self.edit(r),
                size="sm", width=7,
            ).pack(side="left", padx=2)
            ui.button(
                actions, "Excluir", command=lambda r=recipe: self.remove(r),
                variant="danger", size="sm", width=7,
            ).pack(side="left", padx=2)

    # ------------------------------------------------------------------ ações
    def use(self, recipe):
        self.app.set_active_recipe(recipe)
        self.load_recipes()

    def remove(self, recipe):
        if not messagebox.askyesno("Confirma", f"Excluir {recipe['name']}?"):
            return
        if delete_recipe(recipe):
            self.app.reload_active_recipe()
            self.load_recipes()
        else:
            messagebox.showerror("Erro", "Não foi possível excluir a receita.")

    def new_recipe(self):
        self.app.show_recipe_edit(None)

    def edit(self, recipe):
        self.app.show_recipe_edit(recipe)
