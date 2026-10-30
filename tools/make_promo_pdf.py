"""Gera o PDF promocional do SP-IS (A4 retrato, uma página).

Usa dados reais do projeto: as ROIs da receita `200ml` e as imagens de
`data/simulation/`, avaliadas pelo mesmo motor do aplicativo (SSIM por ROI).

Uso:
    python tools/make_promo_pdf.py [saida.pdf]

Requer apenas Pillow e OpenCV (já em requirements.txt).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from paths import ASSETS_DIR, RECIPES_DIR  # noqa: E402
from services.recipe_service import load_reference_image  # noqa: E402
from services.vision_service import evaluate_rois  # noqa: E402

# ---------------------------------------------------------------- identidade
BG = "#0b0e14"
PANEL = "#141820"
PANEL_DEEP = "#0f131a"
BORDER = "#242c3d"
TEXT = "#f0f2f5"
TEXT_DIM = "#8a95a5"
TEXT_MUTED = "#5b6676"
PRIMARY = "#38bdf8"
SUCCESS = "#10b981"
DANGER = "#f43f5e"
ROI_COLORS = ("#38bdf8", "#fbbf24", "#a78bfa")

# ---------------------------------------------------------------- página A4
DPI = 300
PAGE_W = round(210 / 25.4 * DPI)   # 2480 px
PAGE_H = round(297 / 25.4 * DPI)   # 3508 px
MARGIN = 130

FONT_DIR = Path("C:/Windows/Fonts")
FONTS = {
    "light": FONT_DIR / "segoeuil.ttf",
    "regular": FONT_DIR / "segoeui.ttf",
    "semibold": FONT_DIR / "seguisb.ttf",
    "bold": FONT_DIR / "segoeuib.ttf",
    "mono": FONT_DIR / "consola.ttf",
    "mono_bold": FONT_DIR / "consolab.ttf",
}


def font(kind, size):
    path = FONTS.get(kind, FONTS["regular"])
    try:
        return ImageFont.truetype(str(path), size)
    except OSError:
        return ImageFont.load_default()


def hex_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def hex_bgr(value):
    red, green, blue = hex_rgb(value)
    return (blue, green, red)


# ---------------------------------------------------------------- utilidades
def rounded(draw, box, radius, fill=None, outline=None, width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def wrap(text, face, max_width, draw):
    words = text.split()
    lines, current = [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=face) <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def paragraph(draw, xy, text, face, fill, max_width, line_gap=10):
    x, y = xy
    for line in wrap(text, face, max_width, draw):
        draw.text((x, y), line, font=face, fill=fill)
        y += face.size + line_gap
    return y


def tag(draw, xy, text, face, fill, bg=None, pad=(18, 10), outline=None):
    """Etiqueta compacta (chip) com texto centralizado."""
    x, y = xy
    width = draw.textlength(text, font=face)
    box = (x, y, x + width + pad[0] * 2, y + face.size + pad[1] * 2)
    if bg or outline:
        rounded(draw, box, (box[3] - box[1]) // 2, fill=bg, outline=outline, width=2)
    draw.text((x + pad[0], y + pad[1] - 3), text, font=face, fill=fill)
    return box


def glow(canvas, center, radius, color, strength=90):
    """Halo suave (usado atrás da janela do app)."""
    overlay = Image.new("RGB", canvas.size, (0, 0, 0))
    mask = Image.new("L", canvas.size, 0)
    draw = ImageDraw.Draw(mask)
    cx, cy = center
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=strength)
    mask = mask.filter(ImageFilter.GaussianBlur(radius // 2))
    overlay.paste(Image.new("RGB", canvas.size, color), (0, 0), mask)
    return Image.blend(canvas, Image.composite(overlay, canvas, mask), 0.55)


# ---------------------------------------------------------------- dados reais
def load_frame(path):
    buffer = np.fromfile(str(path), dtype=np.uint8)
    image = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
    height, width = image.shape[:2]
    scale = max(640 / width, 480 / height)
    resized = cv2.resize(
        image,
        (max(640, round(width * scale)), max(480, round(height * scale))),
        interpolation=cv2.INTER_AREA,
    )
    top = (resized.shape[0] - 480) // 2
    left = (resized.shape[1] - 640) // 2
    return resized[top:top + 480, left:left + 640]


def load_recipe(name):
    path = RECIPES_DIR / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def draw_rois(image_bgr, details, thickness=3, label=True):
    """Desenha os ROI na imagem (BGR) e devolve PIL RGB."""
    frame = image_bgr.copy()
    for index, entry in enumerate(details or []):
        if entry.get("x1") is None:
            continue
        color = hex_bgr(ROI_COLORS[index % len(ROI_COLORS)])
        cv2.rectangle(
            frame,
            (entry["x1"], entry["y1"]),
            (entry["x2"], entry["y2"]),
            color,
            thickness,
        )
        if label:
            cx = entry["x1"] + 6
            cy = max(22, entry["y1"] - 8)
            cv2.putText(
                frame, str(index + 1), (cx, cy),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2, cv2.LINE_AA,
            )
    return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))


def build_examples():
    """Avalia as imagens de simulação contra a referência real da receita.

    A referência é a imagem salva na receita (`data/images/200ml.jpg`): a peça
    completa, com tampa e rótulo. É o que o aplicativo usa em produção — sem
    isso o ROI do rótulo compararia "sem rótulo × sem rótulo" e aprovaria.
    """
    files = sorted(Path(BASE_DIR / "data" / "simulation").glob("*.jpg"))
    recipe = load_recipe("200ml")
    rois = recipe["rois"]
    frames = [load_frame(path) for path in files]

    reference = load_reference_image(recipe)
    if reference is None:
        reference = frames[-1]

    evaluated = [evaluate_rois(frame, reference, rois) for frame in frames]

    def failed_names(result):
        return [name.lower() for name in result["failed"]]

    ok_index = next((i for i, result in enumerate(evaluated) if result["ok"]), 0)
    single_index = next(
        (i for i, result in enumerate(evaluated)
         if len(result["failed"]) == 1 and i != ok_index),
        None,
    )
    # Prefere a falha de nível (volume) e, na falta, qualquer falha múltipla.
    multi_index = next(
        (i for i, result in enumerate(evaluated)
         if len(result["failed"]) >= 2 and "nível" in failed_names(result)),
        None,
    )
    if multi_index is None:
        multi_index = next(
            (i for i, result in enumerate(evaluated) if len(result["failed"]) >= 2),
            None,
        )
    # Herói: uma falha múltipla com tampa reprovada (garrafa sem tampa).
    hero_index = next(
        (i for i, result in enumerate(evaluated)
         if len(result["failed"]) >= 2 and "tampa" in failed_names(result)
         and i not in (ok_index, single_index, multi_index)),
        None,
    )
    if hero_index is None:
        hero_index = next(
            (i for i, result in enumerate(evaluated)
             if len(result["failed"]) >= 2
             and i not in (ok_index, single_index, multi_index)),
            multi_index if multi_index is not None else ok_index,
        )

    def item(index):
        return frames[index], evaluated[index]

    cards = [
        item(ok_index),
        item(single_index if single_index is not None else ok_index),
        item(multi_index if multi_index is not None else ok_index),
    ]
    return cards, item(hero_index)


# ---------------------------------------------------------------- mock do app
def draw_app_mock(page, draw, box, photo, details, result_text, stats):
    x0, y0, x1, y1 = box
    radius = 26
    rounded(draw, box, radius, fill=PANEL_DEEP, outline=BORDER, width=3)

    header_h = 132
    header_box = (x0, y0, x1, y0 + header_h)
    draw.rounded_rectangle(
        (header_box[0] + 2, header_box[1] + 2, header_box[2] - 2, header_box[3]),
        radius=radius - 4, fill="#0f131a",
    )
    draw.rectangle(
        (header_box[0] + 2, header_box[3] - 30, header_box[2] - 2, header_box[3]), fill="#0f131a"
    )

    face_title = font("bold", 40)
    face_small = font("mono", 26)
    draw.text((x0 + 34, y0 + 34), "Smart Plant - Inspection System", font=face_title, fill=TEXT)
    draw.text(
        (x0 + 34, y0 + 84), "RECEITA EM USO  ·  200 ml", font=face_small, fill=TEXT_DIM
    )

    stat_w = 150
    stat_gap = 14
    total_w = len(stats) * stat_w + (len(stats) - 1) * stat_gap
    sx = x1 - 34 - total_w
    for key, value, color in stats:
        rounded(draw, (sx, y0 + 26, sx + stat_w, y0 + header_h - 26), 10, fill=PANEL, outline=BORDER)
        draw.text((sx + 14, y0 + 38), key, font=font("mono", 21), fill=TEXT_DIM)
        draw.text((sx + 14, y0 + 66), value, font=font("bold", 40), fill=color)
        sx += stat_w + stat_gap

    # sidebar industrial
    sidebar_w = 236
    bar_x0 = x0 + 20
    bar_y0 = y0 + header_h + 24
    bar_y1 = y1 - 24
    items = ("PRINCIPAL", "RECEITAS", "CONFIGURAÇÕES", "USUÁRIOS", "DIAGNÓSTICOS", "AJUDA", "SOBRE")
    face_nav = font("bold", 24)
    step = (bar_y1 - bar_y0) // len(items)
    for index, label in enumerate(items):
        top = bar_y0 + index * step
        active = index == 0
        rounded(
            draw,
            (bar_x0, top + 4, bar_x0 + sidebar_w, top + step - 10),
            8,
            fill=PANEL if active else None,
            outline=PRIMARY if active else BORDER,
            width=3 if active else 2,
        )
        text_width = draw.textlength(label, font=face_nav)
        draw.text(
            (bar_x0 + (sidebar_w - text_width) / 2, top + 22),
            label,
            font=face_nav,
            fill=PRIMARY if active else TEXT_MUTED,
        )

    # canvas com a captura
    canvas_box = (bar_x0 + sidebar_w + 22, bar_y0, x1 - 360, bar_y1)
    rounded(draw, canvas_box, 14, fill="#000000", outline=BORDER, width=2)
    inner = (canvas_box[0] + 10, canvas_box[1] + 10, canvas_box[2] - 10, canvas_box[3] - 10)
    fitted = photo.copy()
    fitted.thumbnail((inner[2] - inner[0], inner[3] - inner[1]), Image.LANCZOS)
    px = inner[0] + (inner[2] - inner[0] - fitted.width) // 2
    py = inner[1] + (inner[3] - inner[1] - fitted.height) // 2
    page.paste(fitted, (px, py))

    # chips flutuantes sobre o vídeo
    face_chip = font("bold", 24)
    tag(draw, (inner[0] + 14, inner[1] + 14), "TRIGGER · BOTÃO + GPIO",
        font("mono", 21), PRIMARY, bg="#0f131a", outline=BORDER)
    live_w = draw.textlength("VÍDEO · AO VIVO", font=face_chip)
    tag(draw, (inner[2] - live_w - 52, inner[1] + 14), "VÍDEO · AO VIVO",
        face_chip, SUCCESS, bg="#0f131a", outline=BORDER)

    # painel de resultado
    panel_box = (x1 - 336, bar_y0, x1 - 22, bar_y1)
    rounded(draw, panel_box, 14, fill=PANEL, outline=BORDER, width=2)
    draw.text((panel_box[0] + 20, panel_box[1] + 20), "ÚLTIMA CAPTURA", font=font("mono", 21), fill=TEXT_DIM)

    ok = all(entry.get("ok") for entry in details)
    face_result = font("bold", 42)
    y = panel_box[1] + 58
    for line in wrap(result_text, face_result, panel_box[2] - panel_box[0] - 40, draw):
        draw.text((panel_box[0] + 20, y), line, font=face_result, fill=SUCCESS if ok else DANGER)
        y += 50

    y += 16
    for index, entry in enumerate(details):
        draw.text(
            (panel_box[0] + 20, y),
            f"{entry['name']}",
            font=font("bold", 28),
            fill=ROI_COLORS[index % len(ROI_COLORS)],
        )
        match = entry.get("match")
        text = f"{match:.1f}%" if isinstance(match, (int, float)) else "—"
        draw.text(
            (panel_box[0] + 20, y + 32),
            f"{text}   janela {entry['min']:g}–{entry['max']:g}%",
            font=font("mono", 23),
            fill=SUCCESS if entry.get("ok") else DANGER,
        )
        y += 76

    button_h = 62
    rounded(
        draw,
        (panel_box[0] + 20, panel_box[3] - button_h - 20, panel_box[2] - 20, panel_box[3] - 20),
        10,
        fill=PRIMARY,
    )
    label = "EXECUTAR CICLO"
    label_w = draw.textlength(label, font=font("bold", 26))
    draw.text(
        (panel_box[0] + 20 + (panel_box[2] - panel_box[0] - 40 - label_w) / 2, panel_box[3] - button_h - 4),
        label, font=font("bold", 26), fill="#04121c",
    )


def draw_metric_chips(draw, xy, details, max_width):
    """Chips "nome valor" na cor do ROI, com o veredito em verde/vermelho."""
    x, y = xy
    face_name = font("bold", 24)
    face_value = font("mono_bold", 25)
    for index, entry in enumerate(details):
        color = ROI_COLORS[index % len(ROI_COLORS)]
        match = entry.get("match")
        value = f"{match:.1f}%".replace(".", ",") if isinstance(match, (int, float)) else "—"
        pad = 12
        width = (draw.textlength(entry["name"], font=face_name) + 10
                 + draw.textlength(value, font=face_value) + pad * 2)
        if x + width > max_width and x != xy[0]:
            x = xy[0]
            y += 44
        rounded(draw, (x, y, x + width, y + 38), 8, fill=PANEL_DEEP, outline=color, width=2)
        draw.text((x + pad, y + 7), entry["name"], font=face_name, fill=color)
        value_x = x + width - pad - draw.textlength(value, font=face_value)
        draw.text(
            (value_x, y + 5), value, font=face_value,
            fill=SUCCESS if entry.get("ok") else DANGER,
        )
        x += width + 10
    return y + 38


def draw_example_card(page, draw, box, photo, result, caption):
    x0, y0, x1, y1 = box
    rounded(draw, box, 18, fill=PANEL, outline=BORDER, width=2)

    image_box = (x0 + 16, y0 + 16, x1 - 16, y0 + 16 + round((x1 - x0 - 32) * 3 / 4))
    rounded(draw, image_box, 10, fill="#000000", outline=BORDER, width=2)
    fitted = photo.copy()
    fitted.thumbnail((image_box[2] - image_box[0], image_box[3] - image_box[1]), Image.LANCZOS)
    page.paste(fitted, (image_box[0], image_box[1]))

    ok = result["ok"]
    face_result = font("bold", 32)
    y = image_box[3] + 18
    for line in wrap(result["result"], face_result, x1 - x0 - 40, draw):
        draw.text((x0 + 20, y), line, font=face_result, fill=SUCCESS if ok else DANGER)
        y += 40

    y += 8
    y = draw_metric_chips(draw, (x0 + 20, y), result["rois"], x1 - 20)
    draw.text((x0 + 20, y + 10), caption, font=font("mono", 20), fill=TEXT_MUTED)


# ---------------------------------------------------------------- poster
def build_poster(output_path, preview_path=None):
    examples, hero = build_examples()
    recipe = load_recipe("200ml")

    page = Image.new("RGB", (PAGE_W, PAGE_H), hex_rgb(BG))
    page = glow(page, (PAGE_W // 2, 1150), 900, hex_rgb("#0d2433"), strength=120)
    draw = ImageDraw.Draw(page)

    # faixa superior
    draw.rectangle((0, 0, PAGE_W, 14), fill=hex_rgb(PRIMARY))

    # marca: logo oficial do SP-IS
    logo = Image.open(ASSETS_DIR / "logo.png").convert("RGBA")
    logo_h = 214
    logo = logo.resize((round(logo.width * logo_h / logo.height), logo_h), Image.LANCZOS)
    page.paste(logo, (MARGIN - 8, 84), logo)

    brand_x = MARGIN + logo.width + 46
    draw.line((brand_x, 112, brand_x, 300), fill=hex_rgb(BORDER), width=3)
    draw.text((brand_x + 34, 132), "Estação de inspeção visual", font=font("bold", 42), fill=TEXT)
    draw.text((brand_x + 34, 186), "para linhas de envase", font=font("bold", 42), fill=TEXT)
    draw.text(
        (brand_x + 34, 246),
        "tampas · níveis · rótulos  —  peça a peça",
        font=font("mono", 27),
        fill=TEXT_DIM,
    )

    badge_text = "INSPEÇÃO VISUAL · TEMPO REAL"
    badge_w = draw.textlength(badge_text, font=font("mono_bold", 30))
    tag(draw, (PAGE_W - MARGIN - badge_w - 40, 104), badge_text,
        font("mono_bold", 30), PRIMARY, bg="#12202b", outline=PRIMARY)

    tagline_face = font("light", 62)
    y = 372
    for line in (
        "Cada peça aprovada ou reprovada em milissegundos.",
        "Três regiões críticas, um padrão de referência e um veredito.",
    ):
        draw.text((MARGIN, y), line, font=tagline_face, fill=TEXT)
        y += 78

    # ---------------- mock do app
    hero_box = (MARGIN, 560, PAGE_W - MARGIN, 1560)
    hero_frame, hero_result = hero
    hero_photo = draw_rois(hero_frame, hero_result["rois"], thickness=3)
    stats = (
        ("TOTAL", "1.284", PRIMARY),
        ("OK", "1.201", SUCCESS),
        ("NOK", "83", DANGER),
        ("APROV.", "93,5%", "#fbbf24"),
        ("TEMPO", "12 ms", "#fbbf24"),
    )
    draw_app_mock(page, draw, hero_box, hero_photo, hero_result["rois"], hero_result["result"], stats)
    draw.text(
        (MARGIN + 6, hero_box[3] + 16),
        "Tela Principal: vídeo ao vivo, ROIs numerados e o resultado de cada região.",
        font=font("regular", 30),
        fill=TEXT_MUTED,
    )

    # ---------------- coluna de texto + diagrama
    top = 1620
    panel_h = 600
    column_w = (PAGE_W - MARGIN * 2 - 70) // 2
    left_box = (MARGIN, top, MARGIN + column_w, top + panel_h)
    right_box = (PAGE_W - MARGIN - column_w, top, PAGE_W - MARGIN, top + panel_h)

    for box in (left_box, right_box):
        rounded(draw, box, 20, fill=PANEL, outline=BORDER, width=2)

    x, y = left_box[0] + 34, left_box[1] + 32
    draw.text((x, y), "O QUE É", font=font("mono_bold", 28), fill=PRIMARY)
    y += 54
    y = paragraph(
        draw, (x, y),
        "O SP-IS é uma estação de inspeção visual para linhas de envase. Ele compara "
        "as regiões críticas de cada garrafa ou pote com o padrão aprovado da receita e "
        "decide, peça a peça, se a embalagem segue para a esteira ou é expulsa.",
        font("regular", 32), TEXT, left_box[2] - x - 34, line_gap=12,
    )
    y += 22
    draw.text((x, y), "SEM OPERADOR OLHANDO A TELA", font=font("mono", 24), fill=TEXT_MUTED)
    y += 46
    for item in (
        "Reprovação dispara o expulsor automaticamente.",
        "Cada inspeção fica no histórico, com imagem e %.",
        "Funciona em plataformas Linux e Windows, sem mudar o código.",
    ):
        draw.ellipse((x, y + 10, x + 12, y + 22), fill=PRIMARY)
        y = paragraph(draw, (x + 30, y), item, font("regular", 29), TEXT_DIM,
                      left_box[2] - x - 70, line_gap=8) + 10

    # diagrama: 3 ROIs
    x, y = right_box[0] + 34, right_box[1] + 32
    draw.text((x, y), "COMO AVALIA", font=font("mono_bold", 28), fill=PRIMARY)
    y += 58
    for index, entry in enumerate(recipe["rois"]):
        color = ROI_COLORS[index % len(ROI_COLORS)]
        rounded(draw, (x, y, x + right_box[2] - x - 34, y + 96), 12, fill=PANEL_DEEP, outline=BORDER)
        draw.ellipse((x + 18, y + 30, x + 54, y + 66), fill=color)
        number_w = draw.textlength(str(index + 1), font=font("bold", 24))
        draw.text((x + 36 - number_w / 2, y + 36), str(index + 1), font=font("bold", 24), fill="#08111a")
        draw.text((x + 76, y + 20), entry["name"], font=font("bold", 34), fill=color)
        draw.text(
            (x + 76, y + 58),
            f"janela {entry['min_match']:g}–{entry['max_match']:g}% de acerto",
            font=font("mono", 24), fill=TEXT_DIM,
        )
        y += 112

    y += 6
    paragraph(
        draw, (x, y),
        "% de acerto = SSIM entre a região atual e a mesma região da imagem de "
        "referência. Aprovado somente quando todos os ROIs ficam dentro da janela.",
        font("regular", 28), TEXT_DIM, right_box[2] - x - 34, line_gap=10,
    )

    # ---------------- exemplos
    examples_top = 2330
    draw.text((MARGIN, examples_top - 74), "EXEMPLOS REAIS DE ANÁLISE",
              font=font("mono_bold", 30), fill=PRIMARY)
    draw.line((MARGIN, examples_top - 26, PAGE_W - MARGIN, examples_top - 26), fill=BORDER, width=2)

    gap = 40
    card_w = (PAGE_W - MARGIN * 2 - gap * 2) // 3
    card_h = 690
    captions = (
        "Peça conforme: rótulo, tampa e nível no padrão.",
        "Rótulo ausente: tampa e nível seguem aprovados.",
        "Volume abaixo do padrão e rótulo ausente.",
    )
    for index, (frame, result) in enumerate(examples):
        x0 = MARGIN + index * (card_w + gap)
        photo = draw_rois(frame, result["rois"], thickness=3)
        draw_example_card(
            page, draw, (x0, examples_top, x0 + card_w, examples_top + card_h),
            photo, result, captions[index],
        )

    # ---------------- recursos
    features_top = examples_top + card_h + 40
    features_h = 210
    features = (
        ("3 ROIs POR RECEITA", "Tampa, nível e rótulo, com nome e janela próprios."),
        ("TRIGGER FLEXÍVEL", "Botão na tela, sensor de presença ou entrada GPIO."),
        ("HISTÓRICO COMPLETO", "Imagem, % por ROI e tempo de cada inspeção."),
        ("MULTIPLATAFORMA", "Linux e Windows: mesma aplicação, sem mudar nada."),
    )
    fw = (PAGE_W - MARGIN * 2 - gap * 3) // 4
    for index, (title, text) in enumerate(features):
        x0 = MARGIN + index * (fw + gap)
        box = (x0, features_top, x0 + fw, features_top + features_h)
        rounded(draw, box, 16, fill=PANEL, outline=BORDER, width=2)
        draw.rectangle((x0 + 24, features_top + 28, x0 + 84, features_top + 34), fill=PRIMARY)
        draw.text((x0 + 24, features_top + 54), title, font=font("mono_bold", 26), fill=TEXT)
        paragraph(draw, (x0 + 24, features_top + 100), text, font("regular", 26),
                  TEXT_DIM, fw - 48, line_gap=8)

    # ---------------- rodapé
    footer_y = PAGE_H - 210
    draw.line((MARGIN, footer_y, PAGE_W - MARGIN, footer_y), fill=BORDER, width=2)

    logo = Image.open(ASSETS_DIR / "logo-dev.png").convert("RGBA")
    ratio = 96 / logo.height
    logo = logo.resize((int(logo.width * ratio), 96), Image.LANCZOS)
    page.paste(logo, (MARGIN, footer_y + 52), logo)

    draw.text((MARGIN, footer_y + 176),
              "Desenvolvido por Autoric Automação e Sistemas · www.autoric.com.br",
              font=font("regular", 27), fill=TEXT_MUTED)

    right_face = font("mono", 26)
    line1 = "Python · CustomTkinter · OpenCV  ·  Linux + Windows"
    line2 = "SP-IS  ·  Inspeção visual de tampas e níveis  ·  v1.1"
    for offset, line, color in ((48, line1, TEXT_DIM), (92, line2, TEXT_MUTED)):
        width = draw.textlength(line, font=right_face)
        draw.text((PAGE_W - MARGIN - width, footer_y + offset), line, font=right_face, fill=color)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    page.save(output_path, "PDF", resolution=DPI)
    if preview_path:
        preview_path = Path(preview_path)
        preview_path.parent.mkdir(parents=True, exist_ok=True)
        page.resize((PAGE_W // 3, PAGE_H // 3), Image.LANCZOS).save(preview_path)
    return output_path


if __name__ == "__main__":
    args = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
    preview_arg = None
    for arg in sys.argv[1:]:
        if arg.startswith("--preview="):
            preview_arg = arg.split("=", 1)[1]
    target = Path(args[0]) if args else BASE_DIR / "SP-IS-promocional.pdf"
    pdf = build_poster(target, preview_arg)
    print("PDF:", pdf)
