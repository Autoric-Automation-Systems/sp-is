class ROISelector:
    HANDLE_SIZE = 6

    def __init__(self, canvas):
        self.canvas = canvas

        # ROIs
        self.original_roi = None  # 🟢 fixo
        self.roi = None           # 🔴 editável

        # desenho
        self.rect = None
        self.handles = []

        # estado mouse
        self.dragging = False
        self.resizing = False
        self.active_handle = None

        canvas.bind("<ButtonPress-1>", self.on_click)
        canvas.bind("<B1-Motion>", self.on_drag)
        canvas.bind("<ButtonRelease-1>", self.on_release)

    # -------- SET ORIGINAL --------
    def set_original(self, roi):
        self.original_roi = roi
        self.roi = roi.copy()  # 👈 começa igual (editável por cima)

    # -------- DRAW --------
    def draw(self):
        # limpa tudo
        if self.rect:
            self.canvas.delete(self.rect)
        for h in self.handles:
            self.canvas.delete(h)
        self.handles.clear()

        # 🟢 ORIGINAL (embaixo - fixo)
        if self.original_roi:
            self.canvas.create_rectangle(
                self.original_roi["x1"],
                self.original_roi["y1"],
                self.original_roi["x2"],
                self.original_roi["y2"],
                outline="green",
                width=2
            )

        # 🔴 EDITÁVEL (por cima)
        if self.roi:
            x1, y1 = self.roi["x1"], self.roi["y1"]
            x2, y2 = self.roi["x2"], self.roi["y2"]

            self.rect = self.canvas.create_rectangle(
                x1, y1, x2, y2,
                outline="red",
                width=2
            )

            # handles (só no editável)
            for (x, y) in [(x1,y1),(x2,y1),(x1,y2),(x2,y2)]:
                h = self.canvas.create_rectangle(
                    x - self.HANDLE_SIZE,
                    y - self.HANDLE_SIZE,
                    x + self.HANDLE_SIZE,
                    y + self.HANDLE_SIZE,
                    fill="yellow"
                )
                self.handles.append(h)

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
            if abs(x - hx) < 10 and abs(y - hy) < 10:
                return name

        return None

    # -------- CLICK --------
    def on_click(self, event):
        if not self.roi:
            # cria novo ROI
            self.roi = {
                "x1": event.x,
                "y1": event.y,
                "x2": event.x,
                "y2": event.y
            }
            self.dragging = True
            return

        handle = self.get_handle(event.x, event.y)

        if handle:
            self.resizing = True
            self.active_handle = handle
        else:
            # mover ROI
            self.dragging = True
            self.offset_x = event.x - self.roi["x1"]
            self.offset_y = event.y - self.roi["y1"]

    # -------- DRAG --------
    def on_drag(self, event):
        if not self.roi:
            return

        if self.resizing:
            if self.active_handle == "tl":
                self.roi["x1"], self.roi["y1"] = event.x, event.y
            elif self.active_handle == "tr":
                self.roi["x2"], self.roi["y1"] = event.x, event.y
            elif self.active_handle == "bl":
                self.roi["x1"], self.roi["y2"] = event.x, event.y
            elif self.active_handle == "br":
                self.roi["x2"], self.roi["y2"] = event.x, event.y

        elif self.dragging:
            w = self.roi["x2"] - self.roi["x1"]
            h = self.roi["y2"] - self.roi["y1"]

            self.roi["x1"] = event.x - self.offset_x
            self.roi["y1"] = event.y - self.offset_y
            self.roi["x2"] = self.roi["x1"] + w
            self.roi["y2"] = self.roi["y1"] + h

    # -------- RELEASE --------
    def on_release(self, event):
        self.dragging = False
        self.resizing = False
        self.active_handle = None

    # -------- FINAL ROI --------
    def get_final_roi(self):
        return self.roi if self.roi else self.original_roi