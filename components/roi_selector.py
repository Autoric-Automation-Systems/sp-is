"""Seleção e edição do ROI sobre o canvas de vídeo."""

HANDLE_SIZE = 6
HANDLE_HITBOX = 10


class ROISelector:
    """Edita o ROI em coordenadas da imagem, mesmo com o canvas reduzido.

    `scale` é a razão canvas/imagem (por exemplo, 0.8 para exibir 640×480 em
    512×384). As coordenadas retornadas sempre pertencem à imagem original.
    """

    def __init__(self, canvas, scale=1.0, image_size=None):
        self.canvas = canvas
        self.scale = float(scale) or 1.0
        self.image_size = image_size

        self.original_roi = None
        self.roi = None

        self.rect = None
        self.handles = []
        self._original_item = None

        self.dragging = False
        self.drawing = False
        self.resizing = False
        self.active_handle = None
        self.offset_x = 0
        self.offset_y = 0

        canvas.bind("<ButtonPress-1>", self.on_click)
        canvas.bind("<B1-Motion>", self.on_drag)
        canvas.bind("<ButtonRelease-1>", self.on_release)

    # -------- SET ORIGINAL --------
    def set_original(self, roi):
        self.original_roi = dict(roi)
        self.roi = dict(roi)
        self._delete_original_item()

    def _delete_original_item(self):
        if self._original_item is not None:
            self.canvas.delete(self._original_item)
            self._original_item = None

    # -------- DRAW --------
    def draw(self):
        if self.original_roi:
            coords = tuple(self._to_canvas(value) for value in (
                self.original_roi["x1"], self.original_roi["y1"],
                self.original_roi["x2"], self.original_roi["y2"],
            ))
            if self._original_item is None:
                self._original_item = self.canvas.create_rectangle(
                    *coords, outline="green", width=2
                )
            else:
                self.canvas.coords(self._original_item, *coords)

        if not self.roi:
            self._delete_editable_items()
            return

        x1, y1, x2, y2 = (self._to_canvas(value) for value in self._coords())

        if self.rect is None:
            self.rect = self.canvas.create_rectangle(x1, y1, x2, y2, outline="red", width=2)
        else:
            self.canvas.coords(self.rect, x1, y1, x2, y2)

        corners = [(x1, y1), (x2, y1), (x1, y2), (x2, y2)]
        if not self.handles:
            for x, y in corners:
                self.handles.append(self.canvas.create_rectangle(
                    x - HANDLE_SIZE, y - HANDLE_SIZE,
                    x + HANDLE_SIZE, y + HANDLE_SIZE,
                    fill="yellow"
                ))
        else:
            for handle, (x, y) in zip(self.handles, corners):
                self.canvas.coords(
                    handle,
                    x - HANDLE_SIZE, y - HANDLE_SIZE,
                    x + HANDLE_SIZE, y + HANDLE_SIZE
                )

    def _delete_editable_items(self):
        if self.rect is not None:
            self.canvas.delete(self.rect)
            self.rect = None
        for handle in self.handles:
            self.canvas.delete(handle)
        self.handles.clear()

    def _coords(self):
        return (
            self.roi["x1"], self.roi["y1"],
            self.roi["x2"], self.roi["y2"],
        )

    def _to_canvas(self, value):
        return int(round(value * self.scale))

    def _to_image(self, value):
        return int(round(value / self.scale))

    # -------- DETECT HANDLE --------
    def get_handle(self, x, y):
        if not self.roi:
            return None

        points = [
            ("tl", self.roi["x1"], self.roi["y1"]),
            ("tr", self.roi["x2"], self.roi["y1"]),
            ("bl", self.roi["x1"], self.roi["y2"]),
            ("br", self.roi["x2"], self.roi["y2"]),
        ]

        for name, hx, hy in points:
            if abs(x - hx) < HANDLE_HITBOX and abs(y - hy) < HANDLE_HITBOX:
                return name

        return None

    def _inside_roi(self, x, y):
        return (
            self.roi is not None
            and self.roi["x1"] <= x <= self.roi["x2"]
            and self.roi["y1"] <= y <= self.roi["y2"]
        )

    def _canvas_size(self):
        """Tamanho lógico (coordenadas da imagem)."""
        if self.image_size:
            return self.image_size
        return (
            int(int(self.canvas.cget("width")) / self.scale),
            int(int(self.canvas.cget("height")) / self.scale),
        )

    def _clamp(self, x, y):
        width, height = self._canvas_size()
        return max(0, min(int(x), width)), max(0, min(int(y), height))

    # -------- CLICK --------
    def on_click(self, event):
        x, y = self._clamp(self._to_image(event.x), self._to_image(event.y))

        if not self.roi:
            self._start_drawing(x, y)
            return

        handle = self.get_handle(x, y)
        if handle:
            self.resizing = True
            self.active_handle = handle
        elif self._inside_roi(x, y):
            self.dragging = True
            self.offset_x = x - self.roi["x1"]
            self.offset_y = y - self.roi["y1"]
        else:
            self._start_drawing(x, y)

    def _start_drawing(self, x, y):
        self.roi = {"x1": x, "y1": y, "x2": x, "y2": y}
        self.drawing = True
        self.dragging = False
        self.resizing = False

    # -------- DRAG --------
    def on_drag(self, event):
        if not self.roi:
            return

        x, y = self._clamp(self._to_image(event.x), self._to_image(event.y))

        if self.drawing:
            self.roi["x2"], self.roi["y2"] = x, y

        elif self.resizing:
            if self.active_handle == "tl":
                self.roi["x1"], self.roi["y1"] = x, y
            elif self.active_handle == "tr":
                self.roi["x2"], self.roi["y1"] = x, y
            elif self.active_handle == "bl":
                self.roi["x1"], self.roi["y2"] = x, y
            elif self.active_handle == "br":
                self.roi["x2"], self.roi["y2"] = x, y

        elif self.dragging:
            width = self.roi["x2"] - self.roi["x1"]
            height = self.roi["y2"] - self.roi["y1"]
            max_x, max_y = self._canvas_size()

            x1 = max(0, min(x - self.offset_x, max_x - width))
            y1 = max(0, min(y - self.offset_y, max_y - height))

            self.roi["x1"], self.roi["y1"] = x1, y1
            self.roi["x2"], self.roi["y2"] = x1 + width, y1 + height

    # -------- RELEASE --------
    def on_release(self, event):
        self.dragging = False
        self.drawing = False
        self.resizing = False
        self.active_handle = None

        if self.roi:
            x1, x2 = sorted((self.roi["x1"], self.roi["x2"]))
            y1, y2 = sorted((self.roi["y1"], self.roi["y2"]))
            self.roi = {"x1": x1, "y1": y1, "x2": x2, "y2": y2}

    # -------- FINAL ROI --------
    def get_final_roi(self):
        roi = self.roi or self.original_roi
        return dict(roi) if roi else None
