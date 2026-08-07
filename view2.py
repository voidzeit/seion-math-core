# -*- coding: utf-8 -*-
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# =====================================================================
# FIX RADICAL: Crear QApplication ANTES de importar cualquier otra cosa
# Esto evita que matplotlib o pyqtgraph rompan Qt al inicializarse.
# =====================================================================
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
app = QApplication(sys.argv)

# --- AHORA SÍ, IMPORTAMOS EL RESTO DE MÓDULOS ---
import os
import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QSlider, QLabel, QComboBox, QCheckBox, 
                             QPushButton, QFileDialog, QMessageBox, QTabWidget)
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QColor, QPalette

# Aislamos matplotlib para que solo genere colores, sin abrir ventanas
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

class E8StudioPro(QMainWindow):
    def __init__(self, file_path):
        super().__init__()
        self.setWindowTitle(f"E8 Lie Algebra Studio PRO - Quadro RTX [{os.path.basename(file_path)}]")
        self.resize(1600, 950)
        
        self.set_dark_theme()

        # Variables de estado del Tensor
        self.dim = 248
        self.so16_dim = 120 # Límite crucial de E8: so(16) vs Espinor
        self.data_u8 = None
        self.current_rgba = None
        self.lut = None
        
        # Parámetros visuales y de render
        self.threshold = 10
        self.alpha_mult = 1.0
        self.slice_x, self.slice_y, self.slice_z = self.dim, self.dim, self.dim
        self.cmap_name = 'magma'
        self.rotation_speed = 0.5

        # Timer para animación
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate_rotation)

        self.init_ui()
        self.load_data(file_path)
        self.update_lut()
        self.apply_render()

    def set_dark_theme(self):
        QApplication.setStyle("Fusion") 
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(30, 30, 30))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(40, 40, 40))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(50, 50, 50))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        self.setPalette(palette)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # ================= PANEL IZQUIERDO: VISOR 3D =================
        self.view = gl.GLViewWidget()
        self.view.setBackgroundColor((15, 15, 20, 255))
        self.view.setCameraPosition(distance=500, elevation=30, azimuth=45)
        main_layout.addWidget(self.view, stretch=7)

        # 1. Caja contenedora global
        self.box = gl.GLBoxItem()
        self.box.setSize(self.dim, self.dim, self.dim)
        self.box.translate(-self.dim/2, -self.dim/2, -self.dim/2)
        self.box.setColor((80, 80, 80, 100))
        self.view.addItem(self.box)

        # 2. Guías de la Subálgebra SO(16)
        self.guide_box = gl.GLBoxItem()
        self.guide_box.setSize(self.so16_dim, self.so16_dim, self.so16_dim)
        self.guide_box.translate(-self.dim/2, -self.dim/2, -self.dim/2)
        self.guide_box.setColor((42, 130, 218, 150))
        self.view.addItem(self.guide_box)
        self.guide_box.setVisible(False)

        # 3. Render de Volumen
        initial_data = np.zeros((self.dim, self.dim, self.dim, 4), dtype=np.ubyte)
        self.volume = gl.GLVolumeItem(initial_data)
        self.volume.translate(-self.dim/2, -self.dim/2, -self.dim/2)
        self.view.addItem(self.volume)

        # ================= PANEL DERECHO: CONTROLES =================
        tabs = QTabWidget()
        main_layout.addWidget(tabs, stretch=2)

        # --- PESTAÑA 1: RENDERIZADO ---
        tab_render = QWidget()
        lay_render = QVBoxLayout(tab_render)

        lay_render.addWidget(QLabel("<b>Mapa de Color (LUT):</b>"))
        self.cmap_combo = QComboBox()
        self.cmap_combo.addItems(['magma', 'inferno', 'plasma', 'viridis', 'cividis', 'ocean', 'twilight_shifted'])
        self.cmap_combo.currentTextChanged.connect(self.change_cmap)
        lay_render.addWidget(self.cmap_combo)

        self.lbl_thresh = QLabel("<b>Umbral de Ruido:</b> 10%")
        self.slider_thresh = self.create_slider(0, 255, self.threshold, self.on_thresh_change)
        lay_render.addWidget(self.lbl_thresh)
        lay_render.addWidget(self.slider_thresh)

        self.lbl_alpha = QLabel("<b>Multiplicador de Densidad:</b> 1.0x")
        self.slider_alpha = self.create_slider(1, 300, 100, self.on_alpha_change)
        lay_render.addWidget(self.lbl_alpha)
        lay_render.addWidget(self.slider_alpha)
        lay_render.addStretch()
        tabs.addTab(tab_render, "Render")

        # --- PESTAÑA 2: GEOMETRÍA Y CORTES ---
        tab_geom = QWidget()
        lay_geom = QVBoxLayout(tab_geom)

        self.chk_guides = QCheckBox("Mostrar Guías Subálgebra SO(16) [Límite 120]")
        self.chk_guides.stateChanged.connect(self.toggle_guides)
        lay_geom.addWidget(self.chk_guides)
        
        lay_geom.addWidget(QLabel("<hr><b>Cortes Volumétricos (Slicing)</b>"))

        self.lbl_x = QLabel(f"Plano A (X): {self.dim}")
        self.slider_x = self.create_slider(1, self.dim, self.dim, self.on_slice_change)
        lay_geom.addWidget(self.lbl_x)
        lay_geom.addWidget(self.slider_x)

        self.lbl_y = QLabel(f"Plano B (Y): {self.dim}")
        self.slider_y = self.create_slider(1, self.dim, self.dim, self.on_slice_change)
        lay_geom.addWidget(self.lbl_y)
        lay_geom.addWidget(self.slider_y)

        self.lbl_z = QLabel(f"Plano C (Z): {self.dim}")
        self.slider_z = self.create_slider(1, self.dim, self.dim, self.on_slice_change)
        lay_geom.addWidget(self.lbl_z)
        lay_geom.addWidget(self.slider_z)
        
        btn_reset_cuts = QPushButton("Resetear Cortes")
        btn_reset_cuts.clicked.connect(self.reset_cuts)
        lay_geom.addWidget(btn_reset_cuts)
        lay_geom.addStretch()
        tabs.addTab(tab_geom, "Geometría")

        # --- PESTAÑA 3: CÁMARA Y EXPORTACIÓN ---
        tab_tools = QWidget()
        lay_tools = QVBoxLayout(tab_tools)

        lay_tools.addWidget(QLabel("<b>Animación Quadro RTX</b>"))
        self.btn_anim = QPushButton("> Iniciar Rotación Continua")
        self.btn_anim.setCheckable(True)
        self.btn_anim.clicked.connect(self.toggle_animation)
        lay_tools.addWidget(self.btn_anim)

        lay_tools.addWidget(QLabel("<hr><b>Exportación</b>"))
        btn_export = QPushButton("Guardar Render Alta Resolución (PNG)")
        btn_export.clicked.connect(self.export_image)
        btn_export.setStyleSheet("background-color: #2a82da; color: white; font-weight: bold; padding: 10px;")
        lay_tools.addWidget(btn_export)
        
        btn_reset_cam = QPushButton("Resetear Cámara (Isométrica)")
        btn_reset_cam.clicked.connect(lambda: self.view.setCameraPosition(distance=500, elevation=30, azimuth=45))
        lay_tools.addWidget(btn_reset_cam)

        lay_tools.addStretch()
        tabs.addTab(tab_tools, "Herramientas")

    def create_slider(self, min_val, max_val, default, callback):
        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(default)
        slider.valueChanged.connect(callback)
        return slider

    def load_data(self, file_path):
        print(f"Cargando tensor MMap: {file_path}...")
        try:
            raw = np.load(file_path, mmap_mode='r')
            data_float = np.abs(np.asanyarray(raw)).astype(np.float32)
            
            d_max = data_float.max()
            if d_max > 0:
                self.data_u8 = ((data_float / d_max) * 255).astype(np.ubyte)
            else:
                self.data_u8 = data_float.astype(np.ubyte)
            
            self.current_rgba = np.empty(self.data_u8.shape + (4,), dtype=np.ubyte)
            print("Tensor preparado para GPU.")
        except Exception as e:
            QMessageBox.critical(self, "Error de Lectura", f"No se pudo cargar el tensor:\n{e}")
            sys.exit(1)

    def update_lut(self):
        try:
            cmap = plt.get_cmap(self.cmap_name)
            self.lut = (cmap(np.linspace(0, 1, 256)) * 255).astype(np.ubyte)
        except Exception as e:
            print(f"Error generando LUT con matplotlib: {e}")
            self.lut = np.zeros((256, 4), dtype=np.ubyte)
            self.lut[:, 0] = np.arange(256)
            self.lut[:, 1] = np.arange(256)
            self.lut[:, 2] = np.arange(256)
            self.lut[:, 3] = 255

    def apply_render(self):
        if self.data_u8 is None or self.lut is None:
            return

        self.current_rgba[...] = self.lut[self.data_u8]

        alpha = self.current_rgba[..., 3].astype(np.float32)
        alpha *= self.alpha_mult
        
        alpha[self.data_u8 < self.threshold] = 0

        if self.slice_x < self.dim: alpha[self.slice_x:, :, :] = 0
        if self.slice_y < self.dim: alpha[:, self.slice_y:, :] = 0
        if self.slice_z < self.dim: alpha[:, :, self.slice_z:] = 0

        self.current_rgba[..., 3] = np.clip(alpha, 0, 255).astype(np.ubyte)
        self.volume.setData(self.current_rgba)

    def change_cmap(self, name):
        self.cmap_name = name
        self.update_lut()
        self.apply_render()

    def on_thresh_change(self, val):
        self.threshold = val
        self.lbl_thresh.setText(f"<b>Umbral de Ruido:</b> {int((val/255)*100)}%")
        self.apply_render()

    def on_alpha_change(self, val):
        self.alpha_mult = val / 100.0
        self.lbl_alpha.setText(f"<b>Multiplicador de Densidad:</b> {self.alpha_mult:.2f}x")
        self.apply_render()

    def on_slice_change(self):
        self.slice_x = self.slider_x.value()
        self.slice_y = self.slider_y.value()
        self.slice_z = self.slider_z.value()
        self.lbl_x.setText(f"Plano A (X): {self.slice_x}")
        self.lbl_y.setText(f"Plano B (Y): {self.slice_y}")
        self.lbl_z.setText(f"Plano C (Z): {self.slice_z}")
        self.apply_render()

    def reset_cuts(self):
        self.slider_x.setValue(self.dim)
        self.slider_y.setValue(self.dim)
        self.slider_z.setValue(self.dim)

    def toggle_guides(self, state):
        self.guide_box.setVisible(state == Qt.Checked)

    def toggle_animation(self, checked):
        if checked:
            self.btn_anim.setText("|| Detener Rotación")
            self.timer.start(16) 
        else:
            self.btn_anim.setText("> Iniciar Rotación Continua")
            self.timer.stop()

    def animate_rotation(self):
        params = self.view.cameraParams()
        self.view.setCameraPosition(azimuth=params['azimuth'] + self.rotation_speed)

    def export_image(self):
        path, _ = QFileDialog.getSaveFileName(self, "Guardar Render", "E8_Render.png", "PNG Images (*.png)")
        if path:
            img = self.view.grabFrameBuffer()
            img.save(path)
            QMessageBox.information(self, "Éxito", f"Render guardado en:\n{path}")


def main():
    # app YA FUE INICIALIZADA EN LA LÍNEA 11, solo llamamos a la ventana
    FILE_PATH = "E8_Exact_v18_2/f_E8.npy" 
    
    if os.path.exists(FILE_PATH):
        window = E8StudioPro(FILE_PATH)
        window.show()
        sys.exit(app.exec_())
    else:
        print(f"Error: No se encontró '{FILE_PATH}'. Ejecuta el generador primero.")

if __name__ == "__main__":
    main()