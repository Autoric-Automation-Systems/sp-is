import tkinter as tk
from components.layout import BaseLayout
from services.recipe_service import list_recipes
from views.recipe_edit import RecipeEditView
from services.recipe_service import delete_recipe
from tkinter import messagebox

class RecipesView:
    def __init__(self, parent, app):
        self.app = app

        layout = BaseLayout(parent, app)

        tk.Label(layout.content, text="RECEITAS", font=("Arial", 18)).pack(pady=10)

        tk.Button(layout.content, text="Nova Receita",
                  command=lambda: self.new_recipe()).pack(pady=5)

        self.list_frame = tk.Frame(layout.content)
        self.list_frame.pack(fill="both", expand=True)

        self.load_recipes()

    def load_recipes(self):
        for w in self.list_frame.winfo_children():
            w.destroy()

        recipes = list_recipes()

        for r in recipes:
            row = tk.Frame(self.list_frame)
            row.pack(fill="x", pady=2)

            tk.Label(row, text=r["name"]).pack(side="left", padx=10)

            tk.Button(row, text="Editar",
                    command=lambda r=r: self.edit(r)).pack(side="right")

            tk.Button(row, text="Excluir",
                    command=lambda r=r: self.remove(r)).pack(side="right")
            
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