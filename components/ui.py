"""Biblioteca padrão de componentes visuais (CustomTkinter).

Todas as telas usam estas fábricas para manter consistência de cores,
tipografia, espaçamento e cantos arredondados.
"""
import tkinter as tk

import customtkinter as ctk

from styles.theme import *

BUTTON_VARIANTS = {
    "primary": {"fg": PRIMARY, "hover": PRIMARY_HOVER, "text": PRIMARY_CONTRAST},
    "secondary": {"fg": BUTTON_BG, "hover": BUTTON_HOVER, "text": TEXT},
    "success": {"fg": SUCCESS, "hover": SUCCESS_HOVER, "text": SUCCESS_CONTRAST},
    "warning": {"fg": WARNING, "hover": WARNING_HOVER, "text": PRIMARY_CONTRAST},
    "danger": {"fg": DANGER, "hover": DANGER_HOVER, "text": TEXT},
    "ghost": {"fg": "transparent", "hover": BUTTON_BG, "text": TEXT_DIM},
}

BUTTON_SIZES = {
    "sm": {"height": 30, "font": (FAMILY, 11, "bold"), "radius": 6},
    "md": {"height": 38, "font": (FAMILY, 12, "bold"), "radius": 8},
    "lg": {"height": 46, "font": (FAMILY, 14, "bold"), "radius": 9},
}

LABEL_KINDS = {
    "title": {"size": 24, "weight": "bold", "color": TEXT},
    "header": {"size": 17, "weight": "bold", "color": TEXT},
    "body": {"size": 13, "weight": "normal", "color": TEXT},
    "bold": {"size": 13, "weight": "bold", "color": TEXT},
    "muted": {"size": 13, "weight": "normal", "color": TEXT_DIM},
    "small": {"size": 11, "weight": "normal", "color": TEXT_DIM},
    "value": {"size": 26, "weight": "bold", "color": TEXT},
    "stat": {"size": 19, "weight": "bold", "color": TEXT},
    "accent": {"size": 13, "weight": "bold", "color": PRIMARY},
}

FRAME_VARIANTS = {
    "bg": BG,
    "card": CARD,
    "header": HEADER_BG,
    "footer": FOOTER_BG,
    "sidebar": SIDEBAR_BG,
    "input": INPUT_BG,
    "transparent": "transparent",
}

_font_cache = {}


def font(family=None, size=13, weight="normal"):
    """CTkFont com cache (precisa ser criada depois do root)."""
    family = family or FAMILY
    key = (family, size, weight)
    if key not in _font_cache:
        _font_cache[key] = ctk.CTkFont(family=family, size=size, weight=weight)
    return _font_cache[key]


def _text_color(kwargs):
    for key in ("text_color", "fg"):
        if key in kwargs:
            return kwargs.pop(key)
    return None


def _font_from_kwargs(kwargs, default):
    value = kwargs.pop("font", None)
    if isinstance(value, tuple):
        family = value[0]
        size = value[1]
        weight = "bold" if len(value) > 2 and "bold" in str(value[2]) else "normal"
        return font(family, max(int(size), 10), weight)
    if isinstance(value, ctk.CTkFont):
        return value
    return default


def frame(parent, variant="bg", **kwargs):
    """Container padrão (bg, card, header, footer, sidebar)."""
    color = FRAME_VARIANTS.get(variant, variant)
    if "bg" in kwargs:
        color = kwargs.pop("bg")
    kwargs.setdefault("corner_radius", 0)
    return ctk.CTkFrame(parent, fg_color=color, **kwargs)


def button(parent, text, command=None, variant="secondary", size="md", **kwargs):
    """Botão padrão com variantes de cor e hover."""
    style = BUTTON_VARIANTS.get(variant, BUTTON_VARIANTS["secondary"])
    sizing = BUTTON_SIZES.get(size, BUTTON_SIZES["md"])

    options = {
        "bg_color": "transparent",
        "height": sizing["height"],
        "corner_radius": sizing["radius"],
        "fg_color": style["fg"],
        "hover_color": style["hover"],
        "text_color": style["text"],
    }
    explicit_font = _font_from_kwargs(kwargs, None)
    options["font"] = explicit_font or font(size=sizing["font"][1], weight="bold")
    options.update(kwargs)
    return ctk.CTkButton(parent, text=text, command=command, **options)


def label(parent, text, kind="body", **kwargs):
    """Label padrão (title, header, body, bold, muted, small, value, stat)."""
    style = LABEL_KINDS.get(kind, LABEL_KINDS["body"])
    text_color = _text_color(kwargs) or style["color"]
    fg_color = kwargs.pop("bg", "transparent")

    options = {
        "bg_color": "transparent",
        "text": text,
        "text_color": text_color,
        "fg_color": fg_color,
        "font": font(size=style["size"], weight=style["weight"]),
        "anchor": "w",
    }
    options["font"] = _font_from_kwargs(kwargs, options["font"])
    options.update(kwargs)
    return ctk.CTkLabel(parent, **options)


def panel(parent, title=None, subtitle=None, padding=16, bg=CARD, pack=True, **kwargs):
    """Cartão com borda e cabeçalho opcional. Retorna o frame (com .content)."""
    outer = ctk.CTkFrame(
        parent,
        bg_color="transparent",
        fg_color=bg,
        corner_radius=10,
        border_width=1,
        border_color=BORDER,
        **kwargs,
    )
    if pack:
        outer.pack(fill="both", expand=True, pady=(0, SPACING_MD))

    content = ctk.CTkFrame(outer, fg_color=bg, corner_radius=0)
    content.pack(fill="both", expand=True, padx=padding, pady=padding)

    if title:
        label(content, title, kind="header", bg=bg).pack(anchor="w")
    if subtitle:
        label(content, subtitle, kind="small", bg=bg).pack(anchor="w", pady=(2, SPACING_SM))

    outer.content = content
    return outer


def paragraph(parent, text, kind="body", padding=12, **kwargs):
    """Texto corrido que quebra linha conforme a largura do pai."""
    style = LABEL_KINDS.get(kind, LABEL_KINDS["body"])
    widget = ctk.CTkLabel(
        parent,
        bg_color="transparent",
        text=text,
        text_color=kwargs.pop("fg", style["color"]),
        fg_color=kwargs.pop("bg", "transparent"),
        font=_font_from_kwargs(kwargs, font(size=style["size"], weight=style["weight"])),
        justify="left",
        anchor="w",
        wraplength=640,
        **kwargs,
    )

    def _sync(event):
        widget.configure(wraplength=max(240, event.width - padding))

    parent.bind("<Configure>", _sync, add="+")
    return widget


def separator(parent, pady=SPACING_SM):
    line = ctk.CTkFrame(parent, fg_color=BORDER, height=1, corner_radius=0)
    line.pack(fill="x", pady=pady)
    return line


def badge(parent, text, color=SUCCESS, bg=None):
    """Etiqueta compacta para status."""
    return ctk.CTkLabel(
        parent,
        bg_color="transparent",
        text=text,
        font=font(size=10, weight="bold"),
        text_color=PRIMARY_CONTRAST if color != DANGER else TEXT,
        fg_color=color if bg is None else bg,
        corner_radius=6,
        padx=8,
        height=22,
    )


def _chars_to_px(chars, padding=24, minimum=110):
    """Converte largura em caracteres (API antiga) para pixels."""
    return max(minimum, int(float(chars) * 8.2) + padding)


def dropdown(parent, variable, values, command=None, width=28, state="readonly"):
    """ComboBox padronizado (width em caracteres)."""
    widget = ctk.CTkComboBox(
        parent,
        bg_color="transparent",
        variable=variable,
        values=list(values) or [""],
        command=command,
        state=state,
        width=_chars_to_px(width),
        height=34,
        corner_radius=6,
        fg_color=INPUT_BG,
        border_color=INPUT_BORDER,
        button_color=BUTTON_BG,
        button_hover_color=BUTTON_HOVER,
        dropdown_fg_color=CARD,
        dropdown_hover_color=BUTTON_BG,
        dropdown_text_color=TEXT,
        text_color=TEXT,
        font=font(size=12),
        dropdown_font=font(size=12),
    )
    return widget


def entry(parent, variable=None, width=24, px_width=None, **kwargs):
    """Campo de texto padrão. `width` em caracteres ou `px_width` em pixels."""
    options = {
        "bg_color": "transparent",
        "width": px_width or _chars_to_px(width, padding=16, minimum=90),
        "height": 34,
        "corner_radius": 6,
        "fg_color": INPUT_BG,
        "border_color": INPUT_BORDER,
        "text_color": TEXT,
        "font": font(size=12),
    }
    if variable is not None:
        options["textvariable"] = variable
    options.update(kwargs)
    return ctk.CTkEntry(parent, **options)


def form_row(parent, row, label_text, widget, hint=None, pady=6):
    """Linha de formulário: rótulo à esquerda, controle à direita."""
    label(parent, label_text, kind="body").grid(row=row, column=0, sticky="w", pady=pady)
    widget.grid(row=row, column=1, sticky="w", padx=(SPACING_MD, 0), pady=pady)
    if hint:
        label(parent, hint, kind="small").grid(
            row=row, column=2, sticky="w", padx=(SPACING_SM, 0), pady=pady
        )
    return widget


def radio(parent, text, variable, value, **kwargs):
    return ctk.CTkRadioButton(
        parent,
        bg_color="transparent",
        text=text,
        variable=variable,
        value=value,
        font=font(size=12),
        text_color=TEXT,
        fg_color=PRIMARY,
        hover_color=PRIMARY_HOVER,
        border_color=BORDER,
        radiobutton_width=18,
        radiobutton_height=18,
        **kwargs,
    )


def checkbox(parent, text, variable, command=None, **kwargs):
    return ctk.CTkCheckBox(
        parent,
        bg_color="transparent",
        text=text,
        variable=variable,
        command=command,
        font=font(size=12),
        text_color=TEXT,
        fg_color=PRIMARY,
        hover_color=PRIMARY_HOVER,
        border_color=BORDER,
        checkbox_width=18,
        checkbox_height=18,
        corner_radius=4,
        **kwargs,
    )


class StatCard:
    """Cartão compacto de estatística com valor atualizável."""

    def __init__(self, parent, title, value="—", accent=PRIMARY, width=110):
        self.frame = ctk.CTkFrame(
            parent,
            bg_color="transparent",
            fg_color=CARD,
            corner_radius=8,
            border_width=1,
            border_color=BORDER,
            width=width,
            height=64,
        )
        self.frame.pack_propagate(False)
        label(self.frame, title.upper(), kind="small", bg=CARD).pack(
            anchor="w", padx=10, pady=(7, 0)
        )
        self.value_label = ctk.CTkLabel(
            self.frame,
            text=value,
            font=font(size=18, weight="bold"),
            text_color=accent,
            fg_color=CARD,
            anchor="w",
        )
        self.value_label.pack(anchor="w", padx=10, pady=(0, 6))

    def set(self, value, color=None):
        self.value_label.configure(text=str(value), text_color=color or self.accent)

    def pack(self, **kwargs):
        self.frame.pack(**kwargs)
        return self

    def grid(self, **kwargs):
        self.frame.grid(**kwargs)
        return self


def scrollable(parent, bg=CARD, **kwargs):
    """Área com rolagem vertical. Retorna (container, frame interno)."""
    container = ctk.CTkScrollableFrame(
        parent,
        fg_color=bg,
        corner_radius=0,
        scrollbar_button_color=BUTTON_BG,
        scrollbar_button_hover_color=BUTTON_HOVER,
        **kwargs,
    )
    return container, container


def configure_styles(root):
    """Aplica o tema escuro do CustomTkinter e estilos de ttk."""
    ctk.set_appearance_mode("dark")
    try:
        from tkinter import ttk

        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure(
            "SPIS.Treeview",
            background=CARD,
            fieldbackground=CARD,
            foreground=TEXT,
            font=FONT_SMALL,
            rowheight=24,
            borderwidth=0,
        )
        style.configure(
            "SPIS.Treeview.Heading",
            background=BUTTON_BG,
            foreground=TEXT,
            font=FONT_BOLD,
            borderwidth=0,
        )
        style.map(
            "SPIS.Treeview",
            background=[("selected", PRIMARY_ACTIVE)],
            foreground=[("selected", TEXT)],
        )
        style.configure("SPIS.TFrame", background=CARD)
        style.configure("TFrame", background=CARD)
        style.configure(
            "TScrollbar",
            background=BUTTON_BG,
            troughcolor=CARD,
            bordercolor=CARD,
            arrowcolor=TEXT_DIM,
        )
    except Exception:
        pass


def canvas(parent, width, height, bg=CANVAS_BG, **kwargs):
    """Canvas Tk dentro do tema (CustomTkinter não tem canvas próprio)."""
    kwargs.pop("bd", None)
    highlight_thickness = kwargs.pop("highlightthickness", 0)
    widget = tk.Canvas(
        parent,
        width=width,
        height=height,
        bg=bg,
        highlightthickness=highlight_thickness,
        bd=0,
        **kwargs,
    )
    return widget
