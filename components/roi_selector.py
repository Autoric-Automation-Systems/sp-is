"""Seleção e edição de múltiplos ROIs sobre o canvas de vídeo."""

from services.recipe_service import ROI_COLORS

HANDLE_SIZE = 6
HANDLE_HITBOX = 10

# Mesma paleta dos cards e dos overlays (sem verde/vermelho: reservados ao resultado).
COLORS = ROI_COLORS
LABEL_OFFSET = 4


class ROISelector:
    """Edita N regiões em coordenadas da imagem, mesmo com o canvas reduzido.

    `scale` é a razão canvas/imagem (por exemplo, 0.8 para exibir 640×480 em
    512×384). As coordenadas retornadas sempre pertencem à imagem original.
    O mouse edita sempre a região ativa (`active`); clicar dentro de outra
    região a torna ativa, o que também funciona em tela touch.
    """

    def __init__(self, canvas, scale=1.0, image_size=None, on_change=None):
        self.canvas = canvas
        self.scale = float(scale) or 1.0
        self.image_size = image_size
        self.on_change = on_change

        self.regions = []
        self.references = []
        self.labels = []
        self.colors = list(COLORS)
        self.active = 0

        self._items = []
        self._reference_items = []
        self._label_items = []

        self._mode = None
        self._handle = None
        self.offset_x = 0
        self.offset_y = 0

        canvas.bind("<ButtonPress-1>", self.on_click)
        canvas.bind("<B1-Motion>", self.on_drag)
        canvas.bind("<ButtonRelease-1>", self.on_release)

    # -------- CONFIGURAÇÃO --------
    def set_regions(self, regions, references=None, labels=None):
        """Define as regiões (lista de retângulos ou None) e os rótulos."""
        self.regions = [dict(region) if region else None for region in regions]
        self.references = [dict(region) if region else None for region in (references or [])]
        self.labels = list(labels or [])
        if self.active >= len(self.regions):
            self.active = max(0, len(self.regions) - 1)
        self._delete_items()
        self.draw()

    def set_active(self, index):
        if 0 <= index < len(self.regions) and index != self.active:
            self.active = index
            self.draw()
            return True
        return False

    def set_region(self, index, roi):
        """Atualiza uma região (usado pelos campos numéricos X/Y)."""
        if not 0 <= index < len(self.regions):
            return
        self.regions[index] = dict(roi) if roi else None
        self.draw()

    def get_region(self, index):
        if not 0 <= index < len(self.regions):
            return None
        region = self.regions[index]
        return dict(region) if region else None

    def get_regions(self):
        return [dict(region) if region else None for region in self.regions]

    def _notify(self):
        if self.on_change is not None:
            try:
                self.on_change(self.active)
            except Exception:
                pass

    # -------- DESENHO --------
    def draw(self):
        self._delete_items()

        for index, reference in enumerate(self.references):
            if not reference:
                continue
            coords = self._canvas_coords(reference)
            self._reference_items.append(
                self.canvas.create_rectangle(*coords, outline="#10b981", dash=(4, 3), width=1)
            )

        for index, region in enumerate(self.regions):
            if not region:
                continue
            color = self.colors[index % len(self.colors)]
            is_active = index == self.active
            coords = self._canvas_coords(region)
            self._items.append(
                self.canvas.create_rectangle(
                    *coords,
                    outline=color,
                    width=3 if is_active else 2,
                )
            )

            label = self._label_text(index)
            if label:
                x1, y1 = coords[0], coords[1]
                self._label_items.append(
                    self.canvas.create_text(
                        x1 + LABEL_OFFSET,
                        max(10, y1 - 10),
                        text=label,
                        fill=color,
                        anchor="w",
                    )
                )

            if is_active:
                for x, y in self._corners(region):
                    self._items.append(
                        self.canvas.create_rectangle(
                            x - HANDLE_SIZE, y - HANDLE_SIZE,
                            x + HANDLE_SIZE, y + HANDLE_SIZE,
                            fill=color,
                        )
                    )

    def _label_text(self, index):
        if index < len(self.labels) and self.labels[index]:
            return f"{index + 1} · {self.labels[index]}"
        return str(index + 1)

    def _canvas_coords(self, region):
        return tuple(
            self._to_canvas(value)
            for value in (region["x1"], region["y1"], region["x2"], region["y2"])
        )

    def _corners(self, region):
        x1, y1, x2, y2 = self._canvas_coords(region)
        return [(x1, y1), (x2, y1), (x1, y2), (x2, y2)]

    def _delete_items(self):
        for item in self._items + self._reference_items + self._label_items:
            try:
                self.canvas.delete(item)
            except Exception:
                pass
        self._items = []
        self._reference_items = []
        self._label_items = []

    def _to_canvas(self, value):
        return int(round(value * self.scale))

    def _to_image(self, value):
        return int(round(value / self.scale))

    # -------- GEOMETRIA --------
    def _active_region(self):
        if 0 <= self.active < len(self.regions):
            return self.regions[self.active]
        return None

    def get_handle(self, x, y):
        region = self._active_region()
        if not region:
            return None

        points = [
            ("tl", region["x1"], region["y1"]),
            ("tr", region["x2"], region["y1"]),
            ("bl", region["x1"], region["y2"]),
            ("br", region["x2"], region["y2"]),
        ]
        for name, hx, hy in points:
            if abs(x - hx) < HANDLE_HITBOX and abs(y - hy) < HANDLE_HITBOX:
                return name
        return None

    @staticmethod
    def _contains(region, x, y):
        return (
            region is not None
            and region["x1"] <= x <= region["x2"]
            and region["y1"] <= y <= region["y2"]
        )

    def _image_size(self):
        if self.image_size:
            return self.image_size
        return (
            int(int(self.canvas.cget("width")) / self.scale),
            int(int(self.canvas.cget("height")) / self.scale),
        )

    def _clamp(self, x, y):
        width, height = self._image_size()
        return max(0, min(int(x), width)), max(0, min(int(y), height))

    def _region_at(self, x, y):
        for index, region in enumerate(self.regions):
            if self._contains(region, x, y):
                return index
        return None

    # -------- EVENTOS --------
    def on_click(self, event):
        x, y = self._clamp(self._to_image(event.x), self._to_image(event.y))

        region = self._active_region()
        if region:
            handle = self.get_handle(x, y)
            if handle:
                self._mode = "resize"
                self._handle = handle
                return
            if self._contains(region, x, y):
                self._mode = "move"
                self.offset_x = x - region["x1"]
                self.offset_y = y - region["y1"]
                return

        other = self._region_at(x, y)
        if other is not None:
            self.set_active(other)
            region = self._active_region()
            self._mode = "move"
            self.offset_x = x - region["x1"]
            self.offset_y = y - region["y1"]
            return

        self.regions[self.active] = {"x1": x, "y1": y, "x2": x, "y2": y}
        self._mode = "draw"
        self._handle = None

    def on_drag(self, event):
        region = self._active_region()
        if not region or self._mode is None:
            return

        x, y = self._clamp(self._to_image(event.x), self._to_image(event.y))

        if self._mode == "draw":
            region["x2"], region["y2"] = x, y
        elif self._mode == "resize":
            if self._handle == "tl":
                region["x1"], region["y1"] = x, y
            elif self._handle == "tr":
                region["x2"], region["y1"] = x, y
            elif self._handle == "bl":
                region["x1"], region["y2"] = x, y
            elif self._handle == "br":
                region["x2"], region["y2"] = x, y
        elif self._mode == "move":
            width = region["x2"] - region["x1"]
            height = region["y2"] - region["y1"]
            max_x, max_y = self._image_size()
            x1 = max(0, min(x - self.offset_x, max_x - width))
            y1 = max(0, min(y - self.offset_y, max_y - height))
            region["x1"], region["y1"] = x1, y1
            region["x2"], region["y2"] = x1 + width, y1 + height

        self.draw()
        self._notify()

    def on_release(self, event):
        region = self._active_region()
        if region:
            x1, x2 = sorted((region["x1"], region["x2"]))
            y1, y2 = sorted((region["y1"], region["y2"]))
            self.regions[self.active] = {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
        self._mode = None
        self._handle = None
        self.draw()
        self._notify()

    # -------- RESULTADO --------
    def get_final_roi(self, index=None):
        """Retângulo da região pedida (padrão: a ativa)."""
        target = self.active if index is None else index
        return self.get_region(target)

