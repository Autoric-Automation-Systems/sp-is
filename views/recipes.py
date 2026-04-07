import tkinter as tk
from components.layout import BaseLayout
from services.recipe_service import list_recipes
from views.recipe_edit import RecipeEditView
from services.recipe_service import delete_recipe
from tkinter import messagebox
from styles.theme import *

class RecipesView:
    def __init__(self, parent, app):
        self.app = app

        layout = BaseLayout(parent, app)

        tk.Label(
            layout.content,
            text="RECEITAS",
            font=FONT_TITLE,
            fg=TEXT,
            bg=BG
        ).pack(pady=(18, 8))

        tk.Button(
            layout.content,
            text="Nova Receita",
            font=BUTTON_FONT,
            fg=BUTTON_TEXT,
            bg=BUTTON_BG,
            activebackground=BUTTON_ACTIVE,
            activeforeground=BUTTON_TEXT,
            bd=0,
            highlightthickness=0,
            cursor="hand2",
            command=lambda: self.new_recipe()
        ).pack(pady=(0, 10))

        self.list_frame = tk.Frame(layout.content, bg=BG)
        self.list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.load_recipes()

    def load_recipes(self):
        for w in self.list_frame.winfo_children():
            w.destroy()

        recipes = list_recipes()

        # Cabeçalho
        header = tk.Frame(
            self.list_frame,
            bg=HEADER_BG,
            bd=0,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        header.pack(fill="x")
        tk.Label(
            header,
            text="Nome",
            font=FONT_HEADER,
            fg=TEXT,
            bg=HEADER_BG,
            anchor="w"
        ).pack(side="left", padx=16, pady=8, fill="x", expand=True)
        tk.Label(
            header,
            text="Ações",
            font=FONT_HEADER,
            fg=TEXT,
            bg=HEADER_BG,
            anchor="e"
        ).pack(side="right", padx=16, pady=8)

        for idx, r in enumerate(recipes):
            bg_color = CARD if idx % 2 == 0 else BG

            row = tk.Frame(
                self.list_frame,
                bg=bg_color,
                bd=0,
                highlightbackground=BORDER,
                highlightthickness=1
            )
            row.pack(fill="x", pady=2)

            tk.Label(
                row,
                text=r["name"],
                font=FONT,
                fg=TEXT,
                bg=bg_color,
                anchor="w"
            ).pack(side="left", padx=16, pady=8, fill="x", expand=True)

            actions = tk.Frame(row, bg=bg_color)
            actions.pack(side="right", padx=10)

            edit_btn = tk.Button(
                actions,
                text="Editar",
                font=BUTTON_FONT,
                fg=BUTTON_TEXT,
                bg=BUTTON_BG,
                activebackground=BUTTON_ACTIVE,
                activeforeground=BUTTON_TEXT,
                bd=0,
                highlightthickness=0,
                cursor="hand2",
                command=lambda r=r: self.edit(r),
                width=8
            )
            edit_btn.pack(side="left", padx=2)

            del_btn = tk.Button(
                actions,
                text="Excluir",
                font=BUTTON_FONT,
                fg=BUTTON_TEXT,
                bg=DANGER,
                activebackground=DANGER_HOVER,
                activeforeground=BUTTON_TEXT,
                bd=0,
                highlightthickness=0,
                cursor="hand2",
                command=lambda r=r: self.remove(r),
                width=8
            )
            del_btn.pack(side="left", padx=2)

    def remove(self, recipe):
        confirm = messagebox.askyesno("Confirma", f"Excluir {recipe['name']}?")
        if confirm:
            delete_recipe(recipe)
            self.load_recipes()
            
    def new_recipe(self):
        self.app.clear()
        RecipeEditView(self.app.container, self.app, None)

    def edit(self, recipe):
        self.app.clear()
        RecipeEditView(self.app.container, self.app, recipe)