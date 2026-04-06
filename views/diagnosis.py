import tkinter as tk
from components.layout import BaseLayout

class DiagnosisView:
    def __init__(self, parent, app):
        layout = BaseLayout(parent, app)

        tk.Label(layout.content, text="DIAGNÓSTICO").pack(pady=50)