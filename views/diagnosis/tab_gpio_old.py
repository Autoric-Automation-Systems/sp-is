"""Aba GPIO - So diagrama com status real dos pinos + barramentos + tree"""
import tkinter as tk
from tkinter import ttk
from styles.theme import *
from processes.gpio_checker import GpioChecker
from .base_tab import BaseTab

# Layout do conector J8 (GPIO 40 pinos) do RPi 4
# Cada tupla: (pino_fisico_esq, nome_esq, bcm_esq, bcm_dir, nome_dir, pino_fisico_dir)
LAYOUT = [
    (1,  "3.3V",    None,  None, "5V",      2),
    (3,  "GPIO2",   2,     3,    "GPIO3",   5),
    (7,  "GPIO4",   4,     14,   "GPIO14",  8),
    (9,  "GND",     None,  15,   "GPIO15", 10),
    (11, "GPIO17",  17,    18,   "GPIO18", 12),
    (13, "GPIO27",  27,    None, "GND",    14),
    (15, "GPIO22",  22,    23,   "GPIO23", 16),
    (17, "3.3V",    None,  24,   "GPIO24", 18),
    (19, "GPIO10",  10,    25,   "GPIO25", 20),
    (21, "GPIO9",   9,     8,    "GPIO8",  22),
    (23, "GPIO11",  11,    7,    "GPIO7",  24),
    (25, "GND",     None,  5,    "GPIO5",  26),
    (27, "GPIO0",   0,     1,    "GPIO1",  28),
    (29, "GPIO5",   5,     13,   "GPIO13", 30),
    (31, "GPIO6",   6,     12,   "GPIO12", 32),
    (33, "GPIO13",  13,    None, "GND",    34),
    (35, "GPIO19",  19,    16,   "GPIO16", 36),
    (37, "GPIO26",  26,    20,   "GPIO20", 38),
    (39, "GND",     None,  21,   "GPIO21", 40),
]

CORES = {"3.3V":"#e74c3c", "5V":"#e67e22", "GND":"#7f8c8d"}

class GpioTab(BaseTab):
    def __init__(self, parent):
        super().__init__(parent)

        # Scroll
        cv = tk.Canvas(self.container, bg=CARD, highlightthickness=0)
        sb = tk.Scrollbar(self.container, orient="vertical", command=cv.yview)
        sf = tk.Frame(cv, bg=CARD)
        sf.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.create_window((0,0), window=sf, anchor="nw")
        cv.configure(yscrollcommand=sb.set)
        cv.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        left = tk.Frame(sf, bg=CARD)
        left.pack(side="left", fill="both", expand=True, padx=(0,8))

        # --- BIBLIOTECAS ---
        bf = tk.LabelFrame(left, text="Bibliotecas GPIO", font=FONT_HEADER,
                           fg=PRIMARY, bg=CARD, bd=0, padx=16, pady=12)
        bf.pack(fill="x", pady=(0,8))
        gi = GpioChecker.gpio_info()
        libs = gi.get("bibliotecas",[])
        for lib in ["RPi.GPIO","gpiozero","wiringPi","pigpio"]:
            f = tk.Frame(bf,bg=CARD); f.pack(fill="x",pady=1)
            tk.Label(f,text=lib,font=FONT_BOLD,fg=TEXT_DIM,bg=CARD,width=14,anchor="w").pack(side="left")
            tk.Label(f,text="Sim" if lib in libs else "Nao",font=FONT,
                     fg=SUCCESS if lib in libs else TEXT_DISABLED,bg=CARD).pack(side="left")
        dok = gi.get("dev_gpiomem",False)
        f = tk.Frame(bf,bg=CARD); f.pack(fill="x",pady=1)
        tk.Label(f,text="/dev/gpiomem",font=FONT_BOLD,fg=TEXT_DIM,bg=CARD,width=14,anchor="w").pack(side="left")
        tk.Label(f,text="Sim" if dok else "Nao",font=FONT,fg=SUCCESS if dok else TEXT_DISABLED,bg=CARD).pack(side="left")

        # Botão para exportar GPIOs
        btn_frame = tk.Frame(bf, bg=CARD)
        btn_frame.pack(fill="x", pady=(8,0))
        btn = tk.Button(btn_frame, text="Exportar GPIOs Comuns", font=FONT_SMALL,
                       bg=BUTTON_BG, fg=TEXT, activebackground=BUTTON_HOVER,
                       command=lambda: self._export_gpios())
        btn.pack(side="left", pady=2)

        # --- DIAGRAMA ---
        df = tk.LabelFrame(left, text="Pinagem GPIO - Status ao Vivo", font=FONT_HEADER,
                           fg=PRIMARY, bg=CARD, bd=0, padx=16, pady=12)
        df.pack(fill="both", expand=True)
        inner = tk.Frame(df, bg=CARD)
        inner.pack(fill="both", expand=True)

        for c,t in enumerate(["Pino","Nome","BCM","","BCM","Nome","Pino"]):
            tk.Label(inner,text=t,font=FONT_SMALL,fg=TEXT_DIM,bg=CARD,
                     width=7 if c!=3 else 2).grid(row=0,column=c,padx=1)

        self.cells = {}
        for i,(fe,ne,be,bd,nd,fd) in enumerate(LAYOUT):
            r = i+1
            bes = str(be) if be is not None else "-"
            bds = str(bd) if bd is not None else "-"

            self.cells[(r,0)] = tk.Label(inner,text=str(fe),font=("Consolas",7),
                                          bg=CARD,width=3,anchor="e")
            self.cells[(r,0)].grid(row=r,column=0,padx=(0,1),sticky="e")
            self.cells[(r,1)] = tk.Label(inner,text=ne,font=("Consolas",7),
                                          bg=CARD,width=7,anchor="w")
            self.cells[(r,1)].grid(row=r,column=1,padx=(0,1),sticky="w")
            self.cells[(r,2)] = tk.Label(inner,text=bes,font=("Consolas",7),
                                          bg=CARD,width=4,anchor="w")
            self.cells[(r,2)].grid(row=r,column=2,padx=(0,1),sticky="w")
            tk.Label(inner,text="|",font=("Consolas",7),fg=BORDER,bg=CARD,width=2).grid(row=r,column=3)
            self.cells[(r,4)] = tk.Label(inner,text=bds,font=("Consolas",7),
                                          bg=CARD,width=4,anchor="e")
            self.cells[(r,4)].grid(row=r,column=4,padx=(1,0),sticky="e")
            self.cells[(r,5)] = tk.Label(inner,text=nd,font=("Consolas",7),
                                          bg=CARD,width=7,anchor="e")
            self.cells[(r,5)].grid(row=r,column=5,padx=(1,0),sticky="e")
            self.cells[(r,6)] = tk.Label(inner,text=str(fd),font=("Consolas",7),
                                          bg=CARD,width=3,anchor="w")
            self.cells[(r,6)].grid(row=r,column=6,padx=(1,0),sticky="w")

        # Legenda
        leg = tk.Frame(inner,bg=CARD)
        leg.grid(row=20,column=0,columnspan=7,sticky="w",pady=(4,0))
        for c,t in [("#e74c3c","3.3V"),("#e67e22","5V"),("#7f8c8d","GND"),
                     ("#2ecc71","HIGH"),("#1a3a1a","LOW"),("#555","Nao export.")]:
            tk.Label(leg,text="■",fg=c,bg=CARD,font=("Segoe UI",10)).pack(side="left",padx=(2,1))
            tk.Label(leg,text=t,fg=TEXT_DIM,bg=CARD,font=FONT_SMALL).pack(side="left",padx=(0,6))

        # --- DIREITA ---
        right = tk.Frame(sf,bg=CARD)
        right.pack(side="right",fill="both",expand=True,padx=(8,0))

        bf2 = tk.LabelFrame(right,text="Barramentos",font=FONT_HEADER,
                            fg=PRIMARY,bg=CARD,bd=0,padx=16,pady=12)
        bf2.pack(fill="x",pady=(0,8))
        self.i2c_lbl = tk.Label(bf2,text="I2C: ---",font=FONT,fg=TEXT,bg=CARD)
        self.i2c_lbl.pack(anchor="w",pady=2)
        self.spi_lbl = tk.Label(bf2,text="SPI: ---",font=FONT,fg=TEXT,bg=CARD)
        self.spi_lbl.pack(anchor="w",pady=2)
        self.ow_lbl = tk.Label(bf2,text="1-Wire: ---",font=FONT,fg=TEXT,bg=CARD)
        self.ow_lbl.pack(anchor="w",pady=2)

        tf = tk.LabelFrame(right,text="GPIOs Exportados",font=FONT_HEADER,
                           fg=PRIMARY,bg=CARD,bd=0,padx=16,pady=12)
        tf.pack(fill="both",expand=True)
        res = GpioChecker.gpio_read_all()
        if not res:
            tk.Label(tf,text="Nenhum GPIO exportado",font=FONT,fg=TEXT_DIM,bg=CARD).pack(anchor="w",pady=4)
            self.tree = None
        else:
            tv = ttk.Treeview(tf,columns=("p","d","v"),show="headings",height=min(len(res),15))
            tv.heading("p",text="#"); tv.heading("d",text="Dir."); tv.heading("v",text="Val.")
            tv.column("p",width=70,anchor="center"); tv.column("d",width=100,anchor="center")
            tv.column("v",width=60,anchor="center")
            ss = ttk.Style()
            ss.configure("Treeview",background=CARD,foreground=TEXT,fieldbackground=CARD,font=FONT_SMALL)
            ss.configure("Treeview.Heading",font=FONT_BOLD,background=BUTTON_BG,foreground=TEXT)
            for p in sorted(res.keys()):
                i=res[p]; tv.insert("","end",values=(p,i["direction"],i["value"]))
            tv.pack(fill="both",expand=True,pady=4)
            self.tree = tv

    def _export_gpios(self):
        """Exporta GPIOs comuns para demonstração"""
        GpioChecker.export_common_gpios()
        self.update()  # Atualiza a tela imediatamente

    def update(self):
        gpios = GpioChecker.gpio_read_all()

        for i,(fe,ne,be,bd,nd,fd) in enumerate(LAYOUT):
            r = i+1

            # Esquerda
            if be is not None:
                if be in gpios:
                    v = gpios[be]["value"]
                    c = "#2ecc71" if v=="1" else "#1a3a1a"
                    self.cells[(r,2)].config(text=f"{be}({v})", fg=c)
                else:
                    c = "#555"
                    self.cells[(r,2)].config(text=str(be), fg=c)
            else:
                c = CORES.get(ne, TEXT_DIM)
                self.cells[(r,2)].config(text="-", fg=c)
            self.cells[(r,0)].config(fg=c)
            self.cells[(r,1)].config(fg=c)

            # Direita
            if bd is not None:
                if bd in gpios:
                    v = gpios[bd]["value"]
                    c = "#2ecc71" if v=="1" else "#1a3a1a"
                    self.cells[(r,4)].config(text=f"{bd}({v})", fg=c)
                else:
                    c = "#555"
                    self.cells[(r,4)].config(text=str(bd), fg=c)
            else:
                c = CORES.get(nd, TEXT_DIM)
                self.cells[(r,4)].config(text="-", fg=c)
            self.cells[(r,5)].config(fg=c)
            self.cells[(r,6)].config(fg=c)

        # Barramentos
        i2c = GpioChecker.i2c_detected()
        self.i2c_lbl.config(text=f"I2C: {len(i2c)} disp.", fg=SUCCESS if i2c else TEXT_DIM)
        spi = GpioChecker.spi_detected()
        self.spi_lbl.config(text=f"SPI: {len(spi)} disp.", fg=SUCCESS if spi else TEXT_DIM)
        ow = GpioChecker.onewire_detected()
        self.ow_lbl.config(text=f"1-Wire: {len(ow)} disp.", fg=SUCCESS if ow else TEXT_DIM)

        if self.tree:
            for item in self.tree.get_children():
                self.tree.delete(item)
            for p in sorted(gpios.keys()):
                i=gpios[p]; self.tree.insert("","end",values=(p,i["direction"],i["value"]))
