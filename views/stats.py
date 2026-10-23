"""Diálogo de estatísticas completas da sessão."""
import customtkinter as ctk
from tkinter import messagebox, ttk

from components import ui
from styles.theme import *


class StatsDialog:
    def __init__(self, parent, app):
        self.app = app
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Estatísticas completas")
        self.window.configure(fg_color=BG)
        self.window.transient(parent)
        self.window.resizable(False, False)

        width, height = 900, 600
        self.window.update_idletasks()
        x = parent.winfo_rootx() + max(0, (parent.winfo_width() - width) // 2)
        y = parent.winfo_rooty() + max(0, (parent.winfo_height() - height) // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")

        header = ctk.CTkFrame(self.window, fg_color=BG, corner_radius=0)
        header.pack(fill="x", padx=20, pady=(16, 8))
        ui.label(header, "ESTATÍSTICAS DA SESSÃO", kind="title").pack(anchor="w")
        self.started_label = ui.label(header, "", kind="small")
        self.started_label.pack(anchor="w")

        self.cards_frame = ctk.CTkFrame(self.window, fg_color=BG, corner_radius=0)
        self.cards_frame.pack(fill="x", padx=20, pady=8)

        tables = ctk.CTkFrame(self.window, fg_color=BG, corner_radius=0)
        tables.pack(fill="both", expand=True, padx=20, pady=8)
        tables.grid_columnconfigure(0, weight=1)
        tables.grid_columnconfigure(1, weight=1)
        tables.grid_rowconfigure(0, weight=1)

        result_panel = ui.panel(tables, title="Por resultado", pack=False, padding=10)
        result_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.result_tree = self._make_tree(
            result_panel.content, ("resultado", "qtd", "%"), ("Resultado", 180), ("Qtd", 60), ("%", 60)
        )

        recipe_panel = ui.panel(tables, title="Por receita", pack=False, padding=10)
        recipe_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        self.recipe_tree = self._make_tree(
            recipe_panel.content,
            ("receita", "total", "ok", "nok", "aprov", "tempo"),
            ("Receita", 150), ("Total", 48), ("OK", 42), ("NOK", 42), ("Aprov.", 60), ("Tempo", 62),
        )

        footer = ctk.CTkFrame(self.window, fg_color=BG, corner_radius=0)
        footer.pack(fill="x", padx=20, pady=(8, 16))
        ui.button(
            footer, "Limpar histórico", command=self._clear, variant="danger", size="sm"
        ).pack(side="left")
        ui.button(footer, "Fechar", command=self.window.destroy, size="sm").pack(side="right")

        self.window.grab_set()
        self.refresh()

    @staticmethod
    def _make_tree(parent, columns, *specs):
        tree = ttk.Treeview(parent, columns=columns, show="headings", style="SPIS.Treeview")
        for column, (title, width) in zip(columns, specs):
            tree.heading(column, text=title)
            tree.column(column, width=width, anchor="center" if width < 120 else "w")
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        return tree

    def refresh(self):
        stats = self.app.history.stats()

        for child in self.cards_frame.winfo_children():
            child.destroy()
        cards = [
            ("Total", stats["total"], PRIMARY),
            ("OK", stats["ok"], SUCCESS),
            ("NOK", stats["nok"], DANGER),
            ("Aprovação", f'{stats["approval"]:.1f}%', SUCCESS if stats["approval"] >= 90 else WARNING),
            ("Tempo médio", f'{stats["avg_ms"]:.0f} ms', WARNING),
        ]
        for title, value, color in cards:
            card = ui.StatCard(self.cards_frame, title, str(value), color, width=128)
            card.frame.configure(height=72)
            card.pack(side="left", padx=4)

        started = stats["started_at"].strftime("%d/%m/%Y %H:%M:%S")
        self.started_label.configure(text=f"Sessão iniciada em {started}")

        for tree in (self.result_tree, self.recipe_tree):
            for item in tree.get_children():
                tree.delete(item)

        total = max(1, stats["total"])
        for result, count in sorted(stats["by_result"].items(), key=lambda item: -item[1]):
            self.result_tree.insert(
                "", "end", values=(result, count, f"{count / total * 100:.1f}")
            )

        for name, entry in sorted(stats["by_recipe"].items()):
            self.recipe_tree.insert(
                "",
                "end",
                values=(
                    name,
                    entry["total"],
                    entry["ok"],
                    entry["nok"],
                    f'{entry["approval"]:.1f}%',
                    f'{entry["avg_ms"]:.0f} ms',
                ),
            )

    def _clear(self):
        if not messagebox.askyesno(
            "Limpar histórico",
            "Deseja apagar o histórico e reiniciar as estatísticas da sessão?",
            parent=self.window,
        ):
            return
        self.app.history.clear()
        self.refresh()
        self.app.notify_history_cleared()
