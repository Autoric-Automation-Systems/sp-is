import sys
content = '''"""Aba GPIO - Bibliotecas, pinagem, barramentos e gpios exportados"""
import tkinter as tk
from tkinter import ttk
from styles.theme import *
from processes.gpio_checker import GpioChecker
from .base_tab import BaseTab


class GpioTab(BaseTab):
    def __init__(self, parent):
        super().__init__(parent)
        canvas = tk.Canvas(self.container, bg=CARD, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.container, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=CARD)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        left = tk.Frame(scroll_frame, bg=CARD)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        libf = self._make_label_frame(left, "Bibliotecas GPIO", pack=False)
        libf.pack(fill="x", pady=(0, 8))
        gi = GpioChecker.gpio_info()
        libs = gi.get("bibliotecas", [])
        for lib in ["RPi.GPIO", "gpiozero", "wiringPi", "pigpio"]:
            ok = lib in libs
            f = tk.Frame(libf, bg=CARD)
            f.pack(fill="x", pady=1)
            tk.Label(f, text=lib, font=FONT_BOLD, fg=TEXT_DIM, bg=CARD, width=14, anchor="w").pack(side="left")
            tk.Label(f, text="Disponivel" if ok else "Nao instalado", font=FONT, fg=SUCCESS if ok else TEXT_DISABLED, bg=CARD).pack(side="left")
        dok = gi.get("dev_gpiomem", False)
        f = tk.Frame(libf, bg=CARD)
        f.pack(fill="x", pady=1)
        tk.Label(f, text="/dev/gpiomem", font=FONT_BOLD, fg=TEXT_DIM, bg=CARD, width=14, anchor="w").pack(side="left")
        tk.Label(f, text="Acessivel" if dok else "Nao encontrado", font=FONT, fg=SUCCESS if dok else TEXT_DISABLED, bg=CARD).pack(side="left")
        pinf = self._make_label_frame(left, "Pinagem GPIO (BCM)", pack=False)
        pinf.pack(fill="both", expand=True, pady=(0, 8))
        inner = tk.Frame(pinf, bg=CARD)
        inner.pack(fill="both", expand=True)
        for col, txt in enumerate(["Pino", "Nome", "GPIO", "", "GPIO", "Nome", "Pino"]):
            tk.Label(inner, text=txt, font=FONT_SMALL, fg=TEXT_DIM, bg=CARD, width=7 if col != 3 else 2).grid(row=0, column=col, padx=1)
        pm = [
            (1,"3.3V","-","-","5V",2),(3,"GPIO2","2","3","GPIO3",4),(5,"GPIO4","4","14","GND",6),
            (7,"GPIO14","14","15","GPIO15",8),(9,"GND","-","18","GPIO18",10),(11,"GPIO17","17","27","GPIO27",12),
            (13,"GPIO27","27","22","GPIO22",14),(15,"GPIO22","22","23","GPIO23",16),(17,"3.3V","-","24","GPIO24",18),
            (19,"GPIO10","10","9","GND",20),(21,"GPIO9","9","25","GPIO25",22),(23,"GPIO11","11","8","GPIO8",24),
            (25,"GND","-","7","GPIO7",26),(27,"GPIO0","0","1","GPIO1",28),(29,"GPIO5","5","6","GPIO6",30),
            (31,"GPIO12","12","13","GPIO13",32),(33,"GPIO26","26","19","GPIO19",34),(35,"GPIO20","20","16","GPIO16",36),
            (37,"GPIO26","26","21","GPIO21",38),(39,"GND","-","28","GPIO28",40)]
        pc = {"3.3V":"#e74c3c","5V":"#e67e22","GND":"#7f8c8d"}
        for i,(fe,ne,be,bd,nd,fd) in enumerate(pm):
            r=i+1; ce=pc.get(ne,"#2ecc71" if be!="-" else TEXT_DIM); cd=pc.get(nd,"#2ecc71" if bd!="-" else TEXT_DIM)
            tk.Label(inner,text=str(fe),font=("Consolas",7),fg=ce,bg=CARD,width=3,anchor="e").grid(row=r,column=0,padx=(0,1),sticky="e")
            tk.Label(inner,text=ne,font=("Consolas",7),fg=TEXT if be!="-" else ce,bg=CARD,width=7,anchor="w").grid(row=r,column=1,padx=(0,1),sticky="w")
            tk.Label(inner,text=be,font=("Consolas",7),fg=TEXT if be!="-" else TEXT_DIM,bg=CARD,width=4,anchor="w").grid(row=r,column=2,padx=(0,1),sticky="w")
            tk.Label(inner,text="|",font=("Consolas",7),fg=BORDER,bg=CARD,width=2).grid(row=r,column=3)
            tk.Label(inner,text=bd,font=("Consolas",7),fg=TEXT if bd!="-" else TEXT_DIM,bg=CARD,width=4,anchor="e").grid(row=r,column=4,padx=(1,0),sticky="e")
            tk.Label(inner,text=nd,font=("Consolas",7),fg=TEXT if bd!="-" else cd,bg=CARD,width=7,anchor="e").grid(row=r,column=5,padx=(1,0),sticky="e")
            tk.Label(inner,text=str(fd),font=("Consolas",7),fg=cd,bg=CARD,width=3,anchor="w").grid(row=r,column=6,padx=(1,0),sticky="w")
        leg=tk.Frame(inner,bg=CARD); leg.grid(row=22,column=0,columnspan=7,sticky="w",pady=(4,0))
        for c,t in [("#e74c3c","3.3V"),("#e67e22","5V"),("#7f8c8d","GND"),("#2ecc71","GPIO")]:
            tk.Label(leg,text="25",fg=c,bg=CARD,font=("Segoe UI",8)).pack(side="left",padx=(2,1))
            tk.Label(leg,text=t,fg=TEXT_DIM,bg=CARD,font=FONT_SMALL).pack(side="left",padx=(0,6))
        right=tk.Frame(scroll_frame,bg=CARD); right.pack(side="right",fill="both",expand=True,padx=(8,0))
        bf=self._make_label_frame(right,"Barramentos",pack=False); bf.pack(fill="x",pady=(0,8))
        self.i2c_lbl=tk.Label(bf,text="I2C: ---",font=FONT,fg=TEXT,bg=CARD); self.i2c_lbl.pack(anchor="w",pady=1)
        self.spi_lbl=tk.Label(bf,text="SPI: ---",font=FONT,fg=TEXT,bg=CARD); self.spi_lbl.pack(anchor="w",pady=1)
        self.ow_lbl=tk.Label(bf,text="1-Wire: ---",font=FONT,fg=TEXT,bg=CARD); self.ow_lbl.pack(anchor="w",pady=1)
        ef=self._make_label_frame(right,"GPIOs Exportados (sysfs)",pack=False); ef.pack(fill="both",expand=True)
        self.gt=None; self._build_tree(ef)
    def _build_tree(self,parent):
        res=GpioChecker.gpio_read_all()
        if not res: tk.Label(parent,text="Nenhum GPIO exportado via sysfs",font=FONT,fg=TEXT_DIM,bg=CARD).pack(anchor="w",pady=4); return
        tree=ttk.Treeview(parent,columns=("pin","dir","val"),show="headings",height=min(len(res),15))
        tree.heading("pin",text="GPIO #"); tree.heading("dir",text="Direcao"); tree.heading("val",text="Valor")
        tree.column("pin",width=70,anchor="center"); tree.column("dir",width=100,anchor="center"); tree.column("val",width=60,anchor="center")
        s=ttk.Style(); s.configure("Treeview",background=CARD,foreground=TEXT,fieldbackground=CARD,font=FONT_SMALL)
        s.configure("Treeview.Heading",font=FONT_BOLD,background=BUTTON_BG,foreground=TEXT)
        for p in sorted(res.keys()): i=res[p]; tree.insert("","end",values=(p,i["direction"],i["value"]))
        tree.pack(fill="both",expand=True,pady=4)
        l2=tk.Frame(parent,bg=CARD); l2.pack(fill="x")
        tk.Label(l2,text="HIGH (1)",fg="#2ecc71",bg=CARD,font=FONT_SMALL).pack(side="left",padx=(0,8))
        tk.Label(l2,text="LOW (0)",fg=TEXT_DIM,bg=CARD,font=FONT_SMALL).pack(side="left")
        self.gt=tree
    def update(self):
        i2c=GpioChecker.i2c_detected(); self.i2c_lbl.config(text=f"I2C: {len(i2c)} disp. - {', '.join(i2c[:8]) if i2c else 'Nenhum'}",fg=SUCCESS if i2c else TEXT_DIM)
        spi=GpioChecker.spi_detected(); self.spi_lbl.config(text=f"SPI: {len(spi)} disp. - {', '.join(spi) if spi else 'Nenhum'}",fg=SUCCESS if spi else TEXT_DIM)
        ow=GpioChecker.onewire_detected(); self.ow_lbl.config(text=f"1-Wire: {len(ow)} dispositivo(s)",fg=SUCCESS if ow else TEXT_DIM)
        if self.gt:
            res=GpioChecker.gpio_read_all()
            for item in self.gt.get_children(): self.gt.delete(item)
            for p in sorted(res.keys()): i=res[p]; self.gt.insert("","end",values=(p,i["direction"],i["value"]))
'''
with open('views/diagnosis/tab_gpio.py', 'w') as f:
    f.write(content)
print('Written to tab_gpio.py')
