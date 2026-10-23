"""SP-IS — shell persistente, rotas e ciclo de vida."""
import logging
import os
import tkinter as tk

import customtkinter as ctk

from components import ui
from components.camera_view import shutdown_camera
from components.footer import Footer
from components.header import Header
from components.sidebar import Sidebar
from services.config_service import load_config, save_config
from services.inspection_service import InspectionHistory
from services.io_service import shutdown_io
from services.recipe_service import list_recipes
from styles.theme import BG
from views.about import AboutPage
from views.diagnosis_view import DiagnosisPage
from views.help import HelpPage
from views.login import LoginDialog
from views.main import MainPage
from views.recipe_edit import RecipeEditPage
from views.recipes import RecipesPage
from views.settings import SettingsPage
from views.users import UsersPage

LOGGER = logging.getLogger(__name__)

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 800

PAGES = {
    "main": MainPage,
    "recipes": RecipesPage,
    "settings": SettingsPage,
    "users": UsersPage,
    "diagnosis": DiagnosisPage,
    "help": HelpPage,
    "about": AboutPage,
    "recipe_edit": RecipeEditPage,
}

# Telas que exigem autenticação.
PROTECTED_ROUTES = {"recipes", "recipe_edit", "settings"}


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.configure(fg_color=BG)
        self.title("SP-IS")
        self.update_idletasks()
        self._apply_window_mode()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        ui.configure_styles(self)

        self.current_user = None
        self.history = InspectionHistory()
        self.config = load_config()
        self.current_recipe = self._resolve_active_recipe()

        self._pages = {}
        self.current_page = None
        self.current_route = None
        self._pending_route = None

        self._build_shell()
        self.show_route("main", force=True)

    # ------------------------------------------------------------------ janela
    def _apply_window_mode(self):
        """windowed (padrão) | fullscreen | zoomed, via SPIS_WINDOW."""
        mode = os.environ.get("SPIS_WINDOW", "windowed").strip().lower()
        try:
            if mode == "fullscreen":
                self.attributes("-fullscreen", True)
            elif mode == "zoomed":
                self.attributes("-zoomed", True)
            else:
                self._apply_windowed_geometry()
        except tk.TclError:
            LOGGER.warning("Modo de janela %r não suportado; usando janela padrão", mode)
            self._apply_windowed_geometry()

    def _apply_windowed_geometry(self):
        """Janela do tamanho da tela, reservando barra de título e de tarefas."""
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        width = min(WINDOW_WIDTH, screen_width)
        reserved = 96 if screen_height <= 800 else 64
        height = max(600, min(WINDOW_HEIGHT, screen_height - reserved))
        self.geometry(f"{width}x{height}+0+0")

    # ------------------------------------------------------------------ shell
    def _build_shell(self):
        self.shell = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.shell.pack(fill="both", expand=True)
        self.shell.grid_rowconfigure(1, weight=1)
        self.shell.grid_columnconfigure(0, weight=1)

        self.header = Header(self.shell, self)
        self.header.frame.grid(row=0, column=0, sticky="ew")

        self.footer = Footer(self.shell, self)
        self.footer.frame.grid(row=2, column=0, sticky="ew")

        body = ctk.CTkFrame(self.shell, fg_color=BG, corner_radius=0)
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)

        self.sidebar = Sidebar(body, self)
        self.sidebar.show()
        self.sidebar.set_user(self.current_user)

        self.page_host = ctk.CTkFrame(body, fg_color=BG, corner_radius=0)
        self.page_host.grid(row=0, column=1, sticky="nsew")
        self.page_host.grid_rowconfigure(0, weight=1)
        self.page_host.grid_columnconfigure(0, weight=1)

        self.refresh_header_stats()

    # ------------------------------------------------------------------ receita ativa
    def _resolve_active_recipe(self):
        recipes = list_recipes()
        name = self.config.get("active_recipe")
        for recipe in recipes:
            if recipe["name"] == name:
                return recipe
        return recipes[0] if recipes else None

    def set_active_recipe(self, recipe):
        self.current_recipe = recipe
        self.config["active_recipe"] = recipe["name"] if recipe else None
        save_config(self.config)

    def reload_active_recipe(self):
        self.config = load_config()
        self.current_recipe = self._resolve_active_recipe()
        name = self.current_recipe["name"] if self.current_recipe else None
        if self.config.get("active_recipe") != name:
            self.config["active_recipe"] = name
            save_config(self.config)

    def set_active_recipe_name(self, name):
        self.config["active_recipe"] = name
        save_config(self.config)
        self.reload_active_recipe()

    # ------------------------------------------------------------------ navegação
    def show_route(self, route, force=False):
        """Troca de página sem reconstruir o shell (evita piscar)."""
        if route not in PAGES:
            LOGGER.warning("Rota desconhecida: %s", route)
            return

        if route in PROTECTED_ROUTES and not self.current_user:
            self._pending_route = route
            self.login()
            return

        if route == self.current_route and not force:
            return  # clique no item já ativo: nenhuma operação

        page = self._pages.get(route)
        if page is None:
            page = PAGES[route](self.page_host, self)
            page.grid(row=0, column=0, sticky="nsew")
            self._pages[route] = page

        previous = self.current_page
        self.current_page = page
        self.current_route = route

        if previous is not None and previous is not page:
            try:
                previous.on_hide()
            except Exception:
                LOGGER.exception("Falha ao ocultar %s", type(previous).__name__)

        page.tkraise()
        self.sidebar.set_active(route)
        try:
            page.on_show()
        except Exception:
            LOGGER.exception("Falha ao exibir %s", type(page).__name__)

    def show_recipe_edit(self, recipe):
        if not self.current_user:
            self._pending_route = "recipes"
            self.login()
            return

        page = self._pages.get("recipe_edit")
        if page is None:
            page = RecipeEditPage(self.page_host, self)
            page.grid(row=0, column=0, sticky="nsew")
            self._pages["recipe_edit"] = page
        page.set_recipe(recipe)
        self.show_route("recipe_edit")

    # ------------------------------------------------------------------ autenticação
    def login(self, next_route=None):
        if self.current_user:
            if next_route:
                self.show_route(next_route)
            return
        if next_route:
            self._pending_route = next_route
        LoginDialog(self, self, next_route=self._pending_route)

    def on_login(self, next_route=None):
        self.sidebar.set_user(self.current_user)
        self.refresh_header_stats()
        route = next_route or self._pending_route or "main"
        self._pending_route = None
        self.show_route(route, force=True)

    def logout(self):
        self.current_user = None
        self.sidebar.set_user(None)
        self._pending_route = None
        if self.current_route in PROTECTED_ROUTES:
            self.show_route("main", force=True)
        else:
            page = self.current_page
            if page is not None and hasattr(page, "on_show"):
                page.on_show()
        self.refresh_header_stats()

    # ------------------------------------------------------------------ estatísticas
    def refresh_header_stats(self):
        """Atualiza apenas o resumo do header (não reconstrói páginas)."""
        try:
            self.header.update_stats(self.history.stats())
        except Exception:
            LOGGER.exception("Falha ao atualizar o resumo do header")

    def notify_history_cleared(self):
        page = self.current_page
        if page is not None and hasattr(page, "on_history_cleared"):
            try:
                page.on_history_cleared()
            except Exception:
                LOGGER.exception("Falha ao limpar a página após reset do histórico")
        self.refresh_header_stats()

    # ------------------------------------------------------------------ encerramento
    def close_pages(self):
        for page in self._pages.values():
            try:
                page.on_close()
            except Exception:
                LOGGER.exception("Falha ao encerrar %s", type(page).__name__)
        self._pages.clear()

    def on_close(self):
        self.close_pages()
        for child in self.winfo_children():
            if isinstance(child, tk.Toplevel):
                child.destroy()
        try:
            self.history.close()
        except Exception:
            LOGGER.exception("Falha ao fechar o banco")
        shutdown_camera()
        shutdown_io()
        self.destroy()


if __name__ == "__main__":
    logging.basicConfig(
        level=os.environ.get("SPIS_LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    App().mainloop()
