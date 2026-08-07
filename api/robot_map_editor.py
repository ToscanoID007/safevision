#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
import tkinter as tk
from tkinter import messagebox

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

class MapEditor:
    def __init__(self, root, file_path):
        self.root = root
        self.file_path = file_path
        self.root.title("ROS Map Editor Fast 2D - " + os.path.basename(file_path))
        
        if HAS_PIL:
            self.pil_orig = Image.open(file_path).convert("L")
            self.width, self.height = self.pil_orig.size
            self.pil_edit = self.pil_orig.copy()
        else:
            messagebox.showerror("Error", "Se requiere PIL/Pillow en la laptop.")
            sys.exit(1)

        self.history = []
        self._save_history_state()

        self.zoom_level = 1.0
        self.pan_x = 0
        self.pan_y = 0
        
        self.current_tool = 'draw'
        self.COLOR_FREE = 254
        self.COLOR_OBSTACLE = 0
        self.COLOR_UNKNOWN = 205
        
        self.current_color = self.COLOR_FREE
        self.brush_size = 5
        self.last_x = None
        self.last_y = None

        self._setup_ui()
        self._bind_shortcuts()
        self._redraw()

    def _save_history_state(self):
        if len(self.history) >= 20:
            self.history.pop(0)
        self.history.append(self.pil_edit.copy())

    def undo(self, event=None):
        if len(self.history) > 1:
            self.history.pop()
            self.pil_edit = self.history[-1].copy()
            self._redraw()

    def set_tool(self, tool):
        self.current_tool = tool
        if tool == 'draw':
            self.btn_draw.config(bg="#0d6efd", fg="white")
            self.btn_pan.config(bg="#343A40", fg="white")
            self.canvas.config(cursor="cross")
        else:
            self.btn_draw.config(bg="#343A40", fg="white")
            self.btn_pan.config(bg="#0d6efd", fg="white")
            self.canvas.config(cursor="fleur")

    def _setup_ui(self):
        top_container = tk.Frame(self.root, bg="#212529")
        top_container.pack(side=tk.TOP, fill=tk.X)

        row1 = tk.Frame(top_container, bg="#212529")
        row1.pack(side=tk.TOP, fill=tk.X, pady=2)

        tk.Label(row1, text=" Modo: ", fg="#ADB5BD", bg="#212529", font=('Helvetica', 9, 'bold')).pack(side=tk.LEFT)
        self.btn_draw = tk.Button(row1, text="Dibujar", bg="#0d6efd", fg="white", command=lambda: self.set_tool('draw'))
        self.btn_draw.pack(side=tk.LEFT, padx=2)
        self.btn_pan = tk.Button(row1, text="Mover Mapa (M)", bg="#343A40", fg="white", command=lambda: self.set_tool('pan'))
        self.btn_pan.pack(side=tk.LEFT, padx=2)

        tk.Label(row1, text=" | Pincel: ", fg="#ADB5BD", bg="#212529", font=('Helvetica', 9, 'bold')).pack(side=tk.LEFT)
        tk.Button(row1, text="Libre (1)", bg="#FFFFFF", fg="black", command=lambda: [self.set_color(self.COLOR_FREE), self.set_tool('draw')]).pack(side=tk.LEFT, padx=2)
        tk.Button(row1, text="Pared (2)", bg="#000000", fg="white", command=lambda: [self.set_color(self.COLOR_OBSTACLE), self.set_tool('draw')]).pack(side=tk.LEFT, padx=2)
        tk.Button(row1, text="Borrador/Gris (E)", bg="#6C757D", fg="white", command=lambda: [self.set_color(self.COLOR_UNKNOWN), self.set_tool('draw')]).pack(side=tk.LEFT, padx=2)

        tk.Label(row1, text=" | Grosor: ", fg="#ADB5BD", bg="#212529", font=('Helvetica', 9, 'bold')).pack(side=tk.LEFT)
        self.brush_scale = tk.Scale(row1, from_=1, to=40, orient=tk.HORIZONTAL, bg="#212529", fg="white", highlightthickness=0, command=self._update_brush)
        self.brush_scale.set(self.brush_size)
        self.brush_scale.pack(side=tk.LEFT, padx=2)

        tk.Label(row1, text=" | Zoom: ", fg="#ADB5BD", bg="#212529", font=('Helvetica', 9, 'bold')).pack(side=tk.LEFT)
        tk.Button(row1, text="+", bg="#343A40", fg="white", width=2, command=lambda: self.zoom_step(1.2)).pack(side=tk.LEFT, padx=1)
        tk.Button(row1, text="-", bg="#343A40", fg="white", width=2, command=lambda: self.zoom_step(0.8)).pack(side=tk.LEFT, padx=1)
        tk.Button(row1, text="Reset", bg="#343A40", fg="white", command=self.zoom_reset).pack(side=tk.LEFT, padx=2)

        row2 = tk.Frame(top_container, bg="#111827")
        row2.pack(side=tk.TOP, fill=tk.X, pady=3)

        tk.Button(row2, text="< Deshacer (Ctrl+Z)", bg="#495057", fg="white", font=('Helvetica', 9, 'bold'), command=self.undo).pack(side=tk.LEFT, padx=10, pady=2)
        
        btn_save = tk.Button(row2, text="[ GUARDAR Y CONCLUIR (Ctrl+S) ]", bg="#198754", fg="white", font=('Helvetica', 10, 'bold'), command=self.save_map)
        btn_save.pack(side=tk.RIGHT, padx=15, pady=2)

        self.canvas = tk.Canvas(self.root, bg="#000000", cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<ButtonPress-1>", self.on_left_click_start)
        self.canvas.bind("<B1-Motion>", self.on_left_click_motion)
        self.canvas.bind("<ButtonRelease-1>", self.on_left_click_end)
        
        self.canvas.bind("<ButtonPress-3>", self.on_pan_start)
        self.canvas.bind("<B3-Motion>", self.on_pan_motion)

        self.root.bind("<MouseWheel>", self.on_zoom)
        self.root.bind("<Button-4>", lambda e: self.zoom_step(1.1))
        self.root.bind("<Button-5>", lambda e: self.zoom_step(0.9))

    def _bind_shortcuts(self):
        self.root.bind("<Control-z>", self.undo)
        self.root.bind("<Control-s>", lambda e: self.save_map())
        self.root.bind("1", lambda e: [self.set_color(self.COLOR_FREE), self.set_tool('draw')])
        self.root.bind("2", lambda e: [self.set_color(self.COLOR_OBSTACLE), self.set_tool('draw')])
        self.root.bind("e", lambda e: [self.set_color(self.COLOR_UNKNOWN), self.set_tool('draw')])
        self.root.bind("E", lambda e: [self.set_color(self.COLOR_UNKNOWN), self.set_tool('draw')])
        self.root.bind("m", lambda e: self.set_tool('pan' if self.current_tool == 'draw' else 'draw'))
        self.root.bind("M", lambda e: self.set_tool('pan' if self.current_tool == 'draw' else 'draw'))
        self.root.bind("<space>", lambda e: self.set_tool('pan' if self.current_tool == 'draw' else 'draw'))

        self.root.bind("<Up>", lambda e: self.pan_by(0, 30))
        self.root.bind("<Down>", lambda e: self.pan_by(0, -30))
        self.root.bind("<Left>", lambda e: self.pan_by(30, 0))
        self.root.bind("<Right>", lambda e: self.pan_by(-30, 0))

    def pan_by(self, dx, dy):
        self.pan_x += dx
        self.pan_y += dy
        self._redraw()

    def set_color(self, val):
        self.current_color = val

    def _update_brush(self, val):
        self.brush_size = int(val)

    def _redraw(self):
        new_w = max(1, int(self.width * self.zoom_level))
        new_h = max(1, int(self.height * self.zoom_level))
        
        resized = self.pil_edit.resize((new_w, new_h), Image.NEAREST)
        self.tk_img = ImageTk.PhotoImage(resized)

        self.canvas.delete("all")
        self.canvas.create_image(self.pan_x, self.pan_y, anchor=tk.NW, image=self.tk_img)

    def _screen_to_image_coords(self, sx, sy):
        ix = int((sx - self.pan_x) / self.zoom_level)
        iy = int((sy - self.pan_y) / self.zoom_level)
        return ix, iy

    def on_left_click_start(self, event):
        if self.current_tool == 'draw':
            self.last_x, self.last_y = self._screen_to_image_coords(event.x, event.y)
            self.paint_pixel(self.last_x, self.last_y)
        else:
            self.on_pan_start(event)

    def on_left_click_motion(self, event):
        if self.current_tool == 'draw':
            cx, cy = self._screen_to_image_coords(event.x, event.y)
            if self.last_x is not None and self.last_y is not None:
                self.paint_line(self.last_x, self.last_y, cx, cy)
            self.last_x, self.last_y = cx, cy
        else:
            self.on_pan_motion(event)

    def on_left_click_end(self, event):
        if self.current_tool == 'draw':
            self.last_x, self.last_y = None, None
            self._save_history_state()

    def paint_pixel(self, x, y):
        r = self.brush_size // 2
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                px, py = x + dx, y + dy
                if 0 <= px < self.width and 0 <= py < self.height:
                    self.pil_edit.putpixel((px, py), self.current_color)
        self._redraw()

    def paint_line(self, x0, y0, x1, y1):
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.paint_pixel(x0, y0)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def on_pan_start(self, event):
        self.pan_start_x = event.x - self.pan_x
        self.pan_start_y = event.y - self.pan_y

    def on_pan_motion(self, event):
        self.pan_x = event.x - self.pan_start_x
        self.pan_y = event.y - self.pan_start_y
        self._redraw()

    def zoom_step(self, factor):
        self.zoom_level = max(0.2, min(20.0, self.zoom_level * factor))
        self._redraw()

    def zoom_reset(self):
        self.zoom_level = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self._redraw()

    def on_zoom(self, event):
        factor = 1.1 if event.delta > 0 else 0.9
        self.zoom_step(factor)

    def save_map(self):
        self.pil_edit.save(self.file_path)
        messagebox.showinfo("Guardado", "El mapa se guardó correctamente.\nPuedes cerrar esta ventana.")
        self.root.destroy()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
    
    path = sys.argv[1]
    if not os.path.exists(path):
        sys.exit(1)

    root = tk.Tk()
    root.geometry("1100x800")
    app = MapEditor(root, path)
    root.mainloop()
