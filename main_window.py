from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLabel, QLineEdit, QComboBox, QDoubleSpinBox, QPushButton, 
    QTextEdit, QGroupBox, QMessageBox, QTabWidget, QScrollArea, QCheckBox,
    QSpinBox, QApplication, QProgressBar, QFrame, QFileDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
import asyncio
import pyautogui
from pynput import keyboard as pynput_kb
import keyboard as kb_global
import pygetwindow as gw
import time
import os

from ocr_engine import OcrManager
from analyzer import analyze_text
from stats_config import ITEM_TYPES, SADDLE_STATS, ARMOR_STATS
from reroll_engine import RerollEngine
from config_manager import save_config, load_config
from overlay import OverlayWindow

ARMOR_OPTIONS = [
    "Magic Find Increased By %",
    "Health Increased By %",
    "Food Increased By",
    "Oxygen Increased By",
    "Swim Speed Increased By %",
    "Elemental Damage Taken Reduced By %",
    "Explosion Damage Taken Reduced By %"
]

SADDLE_OPTIONS = [
    "Melee Damage",
    "Melee Damage Increased By %",
    "Ability Damage",
    "Ability Damage Increase By %",
    "Damage Taken Reduced By %",
    "Nature Damage Taken Reduced By %",
    "Armor Damage Taken Reduced By %",
    "Explosion Damage Taken Reduced By %",
    "Reactive Damage Taken Reduced By %",
    "Impulse Taken Reduced By %",
    "Aggro Reduced By %",
    "Movement Speed Increased By %",
    "Swim Speed Increased By %",
    "Chance To Dodge %"
]

def activate_game_window():
    """Tenta focar a janela do ARK ou ShooterGame."""
    windows = gw.getWindowsWithTitle('ARK')
    if not windows:
        windows = gw.getWindowsWithTitle('ShooterGame')
        
    if windows:
        janela = windows[0]
        try:
            janela.activate()
        except Exception:
            pass
    
    time.sleep(0.5)


class HotkeyListener(QThread):
    f10_pressed = pyqtSignal(int, int)
    f11_pressed = pyqtSignal(int, int)
    f12_pressed = pyqtSignal(int, int)
    f8_pressed = pyqtSignal(int, int)

    def run(self):
        def on_activate_f10():
            x, y = pyautogui.position()
            self.f10_pressed.emit(x, y)
            
        def on_activate_f11():
            x, y = pyautogui.position()
            self.f11_pressed.emit(x, y)
            
        def on_activate_f12():
            x, y = pyautogui.position()
            self.f12_pressed.emit(x, y)
            
        def on_activate_f8():
            x, y = pyautogui.position()
            self.f8_pressed.emit(x, y)

        with pynput_kb.GlobalHotKeys({
                '<f10>': on_activate_f10,
                '<f11>': on_activate_f11,
                '<f12>': on_activate_f12,
                '<f8>': on_activate_f8}) as h:
            h.join()


class OcrWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, x, y, width, height, mode, target_stat, min_value, delay_start=0, item_click_coords=(0,0)):
        super().__init__()
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.mode = mode
        self.target_stat = target_stat
        self.min_value = min_value
        self.delay_start = delay_start
        self.item_click_coords = item_click_coords

    def run(self):
        try:
            if self.delay_start > 0:
                time.sleep(self.delay_start)
                
            activate_game_window()
            
            if self.item_click_coords[0] != 0 or self.item_click_coords[1] != 0:
                pyautogui.click(self.item_click_coords[0], self.item_click_coords[1])
                time.sleep(1.0)
            
            result_text = asyncio.run(self.perform_ocr())
            analysis_result = analyze_text(
                result_text, 
                self.mode, 
                self.target_stat, 
                self.min_value
            )
            self.finished.emit(analysis_result)
        except Exception as e:
            self.error.emit(str(e))

    async def perform_ocr(self):
        manager = OcrManager()
        return await manager.capture_and_recognize(self.x, self.y, self.width, self.height)


class RerollWorker(QThread):
    progress = pyqtSignal(int, dict)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, engine: RerollEngine, delay_start=0):
        super().__init__()
        self.engine = engine
        self.delay_start = delay_start

    def run(self):
        try:
            if self.delay_start > 0:
                time.sleep(self.delay_start)
                
            activate_game_window()
            
            result = self.engine.run(on_progress=self.on_progress_callback)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
            
    def on_progress_callback(self, attempt, current_stats):
        self.progress.emit(attempt, current_stats)

    def stop(self):
        self.engine.stop()


class MainWindow(QMainWindow):
    start_reroll_hotkey_signal = pyqtSignal()
    stop_reroll_hotkey_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ark Omega Reroll - IMBUE STATION by Ly")
        self.resize(700, 850)
        
        self.region_x = 0
        self.region_y = 0
        self.region_w = 400
        self.region_h = 400
        
        self.item_x = 0
        self.item_y = 0
        
        self.reroll_x = 0
        self.reroll_y = 0
        
        self.stat_widgets = []
        self.reroll_worker = None
        self.current_kb_hook = None
        self.stop_kb_hook = None
        
        self.overlay = OverlayWindow()
        
        self.start_reroll_hotkey_signal.connect(self.on_start_reroll_hotkey)
        self.stop_reroll_hotkey_signal.connect(self.stop_reroll)
        
        try:
            self.stop_kb_hook = kb_global.add_hotkey('home', lambda: self.stop_reroll_hotkey_signal.emit())
        except Exception as e:
            print(f"Erro ao registrar hotkey home: {e}")
        
        self.setup_ui()
        self.start_hotkeys()
        self.load_last_config()

    def setup_ui(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        profile_layout = QHBoxLayout()
        self.btn_load_profile = QPushButton("📂 Carregar Perfil")
        self.btn_save_profile = QPushButton("💾 Salvar Perfil")
        self.btn_guide = QPushButton("📖 Como Usar (Guia)")
        self.btn_guide.setStyleSheet("background-color: #0088cc; color: white; font-weight: bold;")
        
        self.btn_load_profile.clicked.connect(self.on_load_profile)
        self.btn_save_profile.clicked.connect(self.on_save_profile)
        self.btn_guide.clicked.connect(self.show_guide)
        
        profile_layout.addWidget(self.btn_load_profile)
        profile_layout.addWidget(self.btn_save_profile)
        profile_layout.addWidget(self.btn_guide)
        main_layout.addLayout(profile_layout)

        self.tabs = QTabWidget()
        
        self.tab_main = QWidget()
        self.tab_test = QWidget()
        
        self.setup_main_tab()
        self.setup_test_tab()
        
        self.tabs.addTab(self.tab_main, "Ferramenta Principal")
        self.tabs.addTab(self.tab_test, "Diagnóstico / Teste")
        
        main_layout.addWidget(self.tabs)
        self.setCentralWidget(central_widget)

    def setup_main_tab(self):
        main_layout = QHBoxLayout(self.tab_main)
        
        # --- COLUNA ESQUERDA ---
        left_layout = QVBoxLayout()
        
        calib_group = QGroupBox("1. Calibração e Posições (Use F8, F10, F11, F12 no jogo)")
        calib_layout = QFormLayout()
        
        self.lbl_item_pos = QLineEdit("Não Definida")
        self.lbl_item_pos.setReadOnly(True)
        self.lbl_reroll_pos = QLineEdit("Não Definida")
        self.lbl_reroll_pos.setReadOnly(True)
        self.lbl_top_left = QLineEdit("Não Definido")
        self.lbl_top_left.setReadOnly(True)
        self.lbl_bot_right = QLineEdit("Não Definido")
        self.lbl_bot_right.setReadOnly(True)
        self.lbl_region_info = QLineEdit("X: 0, Y: 0, L: 400, A: 400")
        self.lbl_region_info.setReadOnly(True)

        calib_layout.addRow("Posição do Item (F10):", self.lbl_item_pos)
        calib_layout.addRow("Botão REROLL (F8):", self.lbl_reroll_pos)
        calib_layout.addRow("Sup. Esq. Área OCR (F11):", self.lbl_top_left)
        calib_layout.addRow("Inf. Dir. Área OCR (F12):", self.lbl_bot_right)
        calib_layout.addRow("Área Capturada:", self.lbl_region_info)
        
        calib_group.setLayout(calib_layout)
        left_layout.addWidget(calib_group)
        
        global_group = QGroupBox("2. Configurações de Reroll Automático")
        global_layout = QFormLayout()
        
        self.spin_max_attempts = QSpinBox()
        self.spin_max_attempts.setRange(1, 9999)
        self.spin_max_attempts.setValue(500)
        
        self.spin_click_delay = QDoubleSpinBox()
        self.spin_click_delay.setRange(0.3, 3.0)
        self.spin_click_delay.setSingleStep(0.1)
        self.spin_click_delay.setValue(0.8)
        self.spin_click_delay.valueChanged.connect(lambda val: self.auto_save_config())
        self.spin_max_attempts.valueChanged.connect(lambda val: self.auto_save_config())

        self.txt_hotkey_start = QLineEdit("F6")
        self.txt_hotkey_start.textChanged.connect(self.update_global_hotkey)
        self.txt_hotkey_start.textChanged.connect(lambda text: self.auto_save_config())
        
        global_layout.addRow("Tentativas Máximas:", self.spin_max_attempts)
        global_layout.addRow("Delay do Bot (segundos):", self.spin_click_delay)
        global_layout.addRow("Hotkey de Início Rápido:", self.txt_hotkey_start)
        
        global_group.setLayout(global_layout)
        left_layout.addWidget(global_group)
        
        # Botões Iniciar / Parar ficam na esquerda, em baixo
        progress_group = QGroupBox("3. Controle e Progresso")
        progress_layout = QVBoxLayout()
        
        self.lbl_reroll_status = QLabel("Aguardando início...")
        self.lbl_reroll_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_reroll_status.setStyleSheet("font-weight: bold; color: blue;")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        
        progress_layout.addWidget(self.lbl_reroll_status)
        progress_layout.addWidget(self.progress_bar)
        
        buttons_layout = QHBoxLayout()
        self.btn_start_reroll = QPushButton("▶ Iniciar Reroll")
        self.btn_start_reroll.setMinimumHeight(40)
        self.btn_start_reroll.setStyleSheet("font-weight: bold; font-size: 14px; background-color: #2e7d32; color: white;")
        self.btn_start_reroll.clicked.connect(lambda: self.start_reroll(from_hotkey=False))
        
        self.btn_stop_reroll = QPushButton("⏹ Parar")
        self.btn_stop_reroll.setMinimumHeight(40)
        self.btn_stop_reroll.setStyleSheet("font-weight: bold; font-size: 14px; background-color: #c62828; color: white;")
        self.btn_stop_reroll.setEnabled(False)
        self.btn_stop_reroll.clicked.connect(self.stop_reroll)
        
        buttons_layout.addWidget(self.btn_start_reroll)
        buttons_layout.addWidget(self.btn_stop_reroll)
        
        progress_layout.addLayout(buttons_layout)
        progress_group.setLayout(progress_layout)
        left_layout.addWidget(progress_group)
        
        # --- Área de Créditos e Logo ---
        credits_layout = QVBoxLayout()
        credits_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_logo = QLabel()
        self.lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Tenta carregar a imagem da pasta do projeto
        from PyQt6.QtGui import QPixmap
        pixmap = QPixmap("logo.png")
        if not pixmap.isNull():
            self.lbl_logo.setPixmap(pixmap.scaled(180, 180, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            self.lbl_logo.setText("[ Salve sua imagem como logo.png na pasta ]")
            self.lbl_logo.setStyleSheet("color: #666666; font-style: italic;")
            
        self.lbl_credits = QLabel("FEITO POR LY - iago.asd02@gmail.com")
        self.lbl_credits.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_credits.setStyleSheet("""
            font-family: 'Impact', 'Arial Black', sans-serif; 
            font-size: 18px; 
            color: #e0e0e0; 
            letter-spacing: 1px;
            margin-top: 10px;
        """)
        
        credits_layout.addWidget(self.lbl_logo)
        credits_layout.addWidget(self.lbl_credits)
        
        left_layout.addLayout(credits_layout)
        
        left_layout.addStretch()
        
        # --- COLUNA DIREITA ---
        right_layout = QVBoxLayout()
        
        type_group = QGroupBox("4. Escolha do Item e Atributos")
        type_layout = QFormLayout()
        
        self.combo_reroll_type = QComboBox()
        self.combo_reroll_type.addItems(ITEM_TYPES)
        self.combo_reroll_type.currentIndexChanged.connect(self.on_item_type_changed)
        type_layout.addRow("Tipo de Item:", self.combo_reroll_type)
        
        type_group.setLayout(type_layout)
        right_layout.addWidget(type_group)
        
        stats_group = QGroupBox("Stats Alvo (Marque o que deseja buscar)")
        stats_layout = QVBoxLayout()
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        self.stats_container = QWidget()
        self.stats_container_layout = QVBoxLayout(self.stats_container)
        self.stats_container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll_area.setWidget(self.stats_container)
        stats_layout.addWidget(self.scroll_area)
        
        stats_group.setLayout(stats_layout)
        right_layout.addWidget(stats_group)
        
        self.populate_stats_list()
        self.update_global_hotkey()
        
        main_layout.addLayout(left_layout, stretch=1)
        main_layout.addLayout(right_layout, stretch=1)

    def setup_test_tab(self):
        layout = QVBoxLayout(self.tab_test)

        analysis_group = QGroupBox("Teste Rápido de OCR (Diagnóstico)")
        analysis_layout = QFormLayout()

        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["Armor", "Saddle comum", "Saddle unique"])
        self.combo_mode.currentIndexChanged.connect(self.update_stat_options)
        
        self.combo_stat = QComboBox()
        
        self.spin_min_val = QDoubleSpinBox()
        self.spin_min_val.setMaximum(99999.0)
        self.spin_min_val.setDecimals(2)
        self.spin_min_val.setValue(100.0)

        analysis_layout.addRow("Modo do Item:", self.combo_mode)
        analysis_layout.addRow("Stat Alvo:", self.combo_stat)
        analysis_layout.addRow("Valor Mínimo:", self.spin_min_val)
        
        analysis_group.setLayout(analysis_layout)
        layout.addWidget(analysis_group)

        self.update_stat_options()

        self.btn_analyze = QPushButton("Capturar, Ler e Analisar")
        self.btn_analyze.setMinimumHeight(50)
        self.btn_analyze.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.btn_analyze.clicked.connect(self.start_analysis)
        layout.addWidget(self.btn_analyze)

        results_group = QGroupBox("Resultados Brutos")
        results_layout = QVBoxLayout()
        self.text_output = QTextEdit()
        self.text_output.setReadOnly(True)
        results_layout.addWidget(self.text_output)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)


    def populate_stats_list(self):
        for i in reversed(range(self.stats_container_layout.count())): 
            widget_to_remove = self.stats_container_layout.itemAt(i).widget()
            self.stats_container_layout.removeWidget(widget_to_remove)
            if widget_to_remove:
                widget_to_remove.setParent(None)
                
        self.stat_widgets.clear()
        
        selected_type = self.combo_reroll_type.currentText()
        
        if "Sela" in selected_type:
            stats_dict = SADDLE_STATS
        else:
            stats_dict = ARMOR_STATS
            
        sorted_stats = sorted(stats_dict.items(), key=lambda item: item[1]["priority"])
        
        for stat_key, stat_data in sorted_stats:
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(5, 5, 5, 5)
            
            checkbox = QCheckBox()
            label = QLabel(stat_data["label"])
            spin_val = QSpinBox()
            spin_val.setRange(0, 9999)
            spin_val.setValue(0)
            
            if stat_data["priority"] == 1:
                label.setStyleSheet("font-weight: bold;")
                row_widget.setStyleSheet("background-color: #2c3e50; border-radius: 5px;")
                
            row_layout.addWidget(checkbox)
            row_layout.addWidget(label)
            row_layout.addWidget(QLabel("Mínimo:"))
            row_layout.addWidget(spin_val)
            
            self.stats_container_layout.addWidget(row_widget)
            
            checkbox.stateChanged.connect(lambda state: self.auto_save_config())
            spin_val.valueChanged.connect(lambda val: self.auto_save_config())
            
            self.stat_widgets.append({
                "stat_key": stat_key,
                "checkbox": checkbox,
                "spin_val": spin_val
            })

    def on_item_type_changed(self):
        self.populate_stats_list()
        self.auto_save_config()

    def update_global_hotkey(self):
        if self.current_kb_hook:
            try:
                kb_global.remove_hotkey(self.current_kb_hook)
            except Exception:
                pass
        
        hotkey = self.txt_hotkey_start.text().strip()
        if hotkey:
            try:
                self.current_kb_hook = kb_global.add_hotkey(hotkey, lambda: self.start_reroll_hotkey_signal.emit())
            except Exception as e:
                print(f"Erro ao registrar hotkey '{hotkey}': {e}")

    def on_start_reroll_hotkey(self):
        if self.btn_start_reroll.isEnabled():
            self.start_reroll(from_hotkey=True)

    def start_hotkeys(self):
        self.hotkey_thread = HotkeyListener()
        self.hotkey_thread.f10_pressed.connect(self.on_f10)
        self.hotkey_thread.f11_pressed.connect(self.on_f11)
        self.hotkey_thread.f12_pressed.connect(self.on_f12)
        self.hotkey_thread.f8_pressed.connect(self.on_f8)
        self.hotkey_thread.start()

    def update_stat_options(self):
        mode = self.combo_mode.currentText()
        self.combo_stat.clear()
        if mode == "Armor":
            self.combo_stat.addItems(ARMOR_OPTIONS)
        else:
            self.combo_stat.addItems(SADDLE_OPTIONS)

    def on_f10(self, x, y):
        self.item_x = x
        self.item_y = y
        self.lbl_item_pos.setText(f"X: {x}, Y: {y}")
        self.auto_save_config()
        
    def on_f8(self, x, y):
        self.reroll_x = x
        self.reroll_y = y
        self.lbl_reroll_pos.setText(f"X: {x}, Y: {y}")
        self.auto_save_config()

    def on_f11(self, x, y):
        self.lbl_top_left.setText(f"X: {x}, Y: {y}")
        self.region_x = x
        self.region_y = y
        self.update_region_info()
        self.auto_save_config()

    def on_f12(self, x, y):
        self.lbl_bot_right.setText(f"X: {x}, Y: {y}")
        self.region_w = max(1, x - self.region_x)
        self.region_h = max(1, y - self.region_y)
        self.update_region_info()
        self.auto_save_config()

    def update_region_info(self):
        self.lbl_region_info.setText(
            f"X: {self.region_x}, Y: {self.region_y}, L: {self.region_w}, A: {self.region_h}"
        )

    def auto_save_config(self):
        data = self.collect_config_data()
        save_config("last_config.json", data)

    # --- Persistência de Configuração ---
    def collect_config_data(self) -> dict:
        target_stats = []
        for w_dict in self.stat_widgets:
            if w_dict["checkbox"].isChecked():
                target_stats.append({
                    "stat_name": w_dict["stat_key"],
                    "min_value": float(w_dict["spin_val"].value())
                })
                
        return {
            "item_click_coords": [self.item_x, self.item_y],
            "reroll_button_coords": [self.reroll_x, self.reroll_y],
            "ocr_region": {
                "top": self.region_y,
                "left": self.region_x,
                "width": self.region_w,
                "height": self.region_h
            },
            "item_type": self.combo_reroll_type.currentText(),
            "selected_stats": target_stats,
            "max_attempts": self.spin_max_attempts.value(),
            "click_delay": self.spin_click_delay.value(),
            "start_hotkey": self.txt_hotkey_start.text()
        }

    def apply_config_data(self, data: dict):
        if not data:
            return
            
        coords = data.get("item_click_coords", [0, 0])
        self.item_x, self.item_y = coords[0], coords[1]
        self.lbl_item_pos.setText(f"X: {self.item_x}, Y: {self.item_y}")
        
        reroll_coords = data.get("reroll_button_coords", [0, 0])
        self.reroll_x, self.reroll_y = reroll_coords[0], reroll_coords[1]
        self.lbl_reroll_pos.setText(f"X: {self.reroll_x}, Y: {self.reroll_y}")
        
        region = data.get("ocr_region", {})
        self.region_y = region.get("top", 0)
        self.region_x = region.get("left", 0)
        self.region_w = region.get("width", 400)
        self.region_h = region.get("height", 400)
        self.lbl_top_left.setText(f"X: {self.region_x}, Y: {self.region_y}")
        self.lbl_bot_right.setText(f"X: {self.region_x + self.region_w}, Y: {self.region_y + self.region_h}")
        self.update_region_info()
        
        item_type = data.get("item_type")
        if item_type:
            idx = self.combo_reroll_type.findText(item_type)
            if idx >= 0:
                self.combo_reroll_type.setCurrentIndex(idx)
                
        self.spin_max_attempts.setValue(data.get("max_attempts", 500))
        self.spin_click_delay.setValue(data.get("click_delay", 0.8))
        self.txt_hotkey_start.setText(data.get("start_hotkey", "F6"))
        
        selected_stats = data.get("selected_stats", [])
        selected_dict = {s["stat_name"]: s["min_value"] for s in selected_stats}
        
        for w_dict in self.stat_widgets:
            stat_name = w_dict["stat_key"]
            if stat_name in selected_dict:
                w_dict["checkbox"].setChecked(True)
                w_dict["spin_val"].setValue(int(selected_dict[stat_name]))
            else:
                w_dict["checkbox"].setChecked(False)
                w_dict["spin_val"].setValue(0)

    def on_load_profile(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Carregar Perfil JSON", "", "JSON Files (*.json)")
        if filepath:
            data = load_config(filepath)
            self.apply_config_data(data)

    def on_save_profile(self):
        filepath, _ = QFileDialog.getSaveFileName(self, "Salvar Perfil JSON", "", "JSON Files (*.json)")
        if filepath:
            data = self.collect_config_data()
            save_config(filepath, data)

    def load_last_config(self):
        data = load_config("last_config.json")
        self.apply_config_data(data)

    def closeEvent(self, event):
        data = self.collect_config_data()
        save_config("last_config.json", data)
        if self.current_kb_hook:
            try:
                kb_global.remove_hotkey(self.current_kb_hook)
            except Exception:
                pass
        if self.stop_kb_hook:
            try:
                kb_global.remove_hotkey(self.stop_kb_hook)
            except Exception:
                pass
        self.overlay.close()
        event.accept()

    # --- Métodos de Teste ---
    def start_analysis(self):
        mode = self.combo_mode.currentText()
        target_stat = self.combo_stat.currentText()
        min_val = self.spin_min_val.value()

        if not target_stat:
            QMessageBox.warning(self, "Erro", "Selecione um Stat Alvo válido.")
            return

        self.showMinimized()

        self.btn_analyze.setEnabled(False)
        self.btn_analyze.setText("Analisando...")
        self.text_output.clear()
        
        self.worker = OcrWorker(
            self.region_x, self.region_y, self.region_w, self.region_h, 
            mode, target_stat, min_val, 
            delay_start=2,
            item_click_coords=(self.item_x, self.item_y)
        )
        self.worker.finished.connect(self.on_analysis_finished)
        self.worker.error.connect(self.on_analysis_error)
        self.worker.start()

    def on_analysis_finished(self, result: dict):
        self.btn_analyze.setEnabled(True)
        self.btn_analyze.setText("Capturar, Ler e Analisar")

        mode = self.combo_mode.currentText()
        target_stat = self.combo_stat.currentText()
        min_val = self.spin_min_val.value()

        status_text = "<span style='color: green;'>APROVADO</span>" if result['approved'] else "<span style='color: red;'>REPROVADO</span>"
        output_html = f"<h2>Resultado: {status_text}</h2>"
        output_html += f"<b>Motivo:</b> {result['reason']}<br><hr>"
        
        output_html += f"<b>Área de Captura (OCR):</b> {self.lbl_region_info.text()}<br>"
        output_html += f"<b>Modo Selecionado:</b> {mode}<br>"
        output_html += f"<b>Stat Alvo Selecionado:</b> {target_stat}<br>"
        output_html += f"<b>Valor Mínimo Requerido:</b> {min_val}<br><hr>"
        
        output_html += f"<b>Linha Encontrada:</b> {result.get('found_line', 'Nenhuma')}<br>"
        output_html += f"<b>Valor Numérico Extraído:</b> {result['value_found'] if result['value_found'] is not None else 'N/A'}<br><hr>"
        output_html += f"<b>Texto Analisado (Filtro):</b><pre>{result['parsed_text']}</pre><hr>"
        output_html += f"<b>Texto Bruto Completo (OCR):</b><pre>{result['raw_text']}</pre>"

        self.text_output.setHtml(output_html)

    def on_analysis_error(self, err_msg: str):
        self.btn_analyze.setEnabled(True)
        self.btn_analyze.setText("Capturar, Ler e Analisar")
        QMessageBox.critical(self, "Erro de Execução", f"Ocorreu um erro durante a leitura OCR:\n{err_msg}")

    # --- Métodos do RerollEngine ---
    def start_reroll(self, from_hotkey=False):
        if self.item_x == 0 and self.item_y == 0:
            if not from_hotkey:
                QMessageBox.warning(self, "Calibração Faltando", "Por favor, defina a posição do item usando F10 na aba de Calibração.")
            return
            
        if self.reroll_x == 0 and self.reroll_y == 0:
            if not from_hotkey:
                QMessageBox.warning(self, "Calibração Faltando", "Por favor, defina a posição do botão REROLL usando F8 na aba de Calibração.")
            return
            
        if self.region_w <= 1 or self.region_h <= 1:
            if not from_hotkey:
                QMessageBox.warning(self, "Calibração Faltando", "Por favor, defina a área do OCR (F11 e F12) na aba de Calibração.")
            return

        target_stats = []
        for w_dict in self.stat_widgets:
            if w_dict["checkbox"].isChecked():
                target_stats.append({
                    "stat_name": w_dict["stat_key"],
                    "min_value": float(w_dict["spin_val"].value())
                })
                
        if not target_stats:
            if not from_hotkey:
                QMessageBox.warning(self, "Nenhum Alvo", "Por favor, marque pelo menos um Stat na lista de alvos.")
            return

        max_att = self.spin_max_attempts.value()
        c_delay = self.spin_click_delay.value()
        
        item_type_ui = self.combo_reroll_type.currentText()
        internal_item_type = "Saddle unique" if "Sela" in item_type_ui else "Armor"
        
        engine = RerollEngine(
            item_click_coords=(self.item_x, self.item_y),
            reroll_button_coords=(self.reroll_x, self.reroll_y),
            ocr_region={
                "left": self.region_x,
                "top": self.region_y,
                "width": self.region_w,
                "height": self.region_h
            },
            target_stats=target_stats,
            item_type=internal_item_type,
            max_attempts=max_att,
            click_delay=c_delay
        )
        
        delay = 0 if from_hotkey else 2
        if not from_hotkey:
            self.showMinimized()
            
        self.reroll_worker = RerollWorker(engine, delay_start=delay)
        self.reroll_worker.progress.connect(self.on_reroll_progress)
        self.reroll_worker.finished.connect(self.on_reroll_finished)
        self.reroll_worker.error.connect(self.on_reroll_error)
        
        self.progress_bar.setMaximum(max_att)
        self.progress_bar.setValue(0)
        
        self.btn_start_reroll.setEnabled(False)
        self.btn_stop_reroll.setEnabled(True)
        self.lbl_reroll_status.setText("Iniciando Reroll...")
        self.lbl_reroll_status.setStyleSheet("font-weight: bold; color: orange;")
        
        self.overlay.show()
        self.overlay.position_window()
        self.overlay.update_status(0, max_att, "", "", "", "rolling")
        
        self.reroll_worker.start()

    def stop_reroll(self):
        if self.reroll_worker:
            self.reroll_worker.stop()
            self.lbl_reroll_status.setText("Parando... aguarde a iteração atual finalizar.")
            self.overlay.update_status(self.progress_bar.value(), self.spin_max_attempts.value(), "", "", "", "cancelled")
            QTimer.singleShot(3000, self.overlay.hide)

    def on_reroll_progress(self, attempt: int, stats: dict):
        self.progress_bar.setValue(attempt)
        
        status_lines = []
        for stat_name, analysis in stats.items():
            if "error" in stats:
                status_lines.append(f"Erro: {stats['error']}")
                break
            
            val = analysis.get('value_found', 'N/A')
            status = "OK" if analysis.get('approved') else "X"
            status_lines.append(f"[{status}] {stat_name}: {val}")
            
        summary = " | ".join(status_lines)
        self.lbl_reroll_status.setText(f"Tentativa {attempt} - {summary}")

        # Update overlay
        if stats and "error" not in stats:
            stat_name = list(stats.keys())[0]
            analysis = stats[stat_name]
            
            min_val = 0
            for w in self.stat_widgets:
                if w["stat_key"] == stat_name:
                    min_val = w["spin_val"].value()
                    break
                    
            val = analysis.get('value_found')
            if val is None:
                self.overlay.update_status(attempt, self.spin_max_attempts.value(), stat_name, "", min_val, "not_found")
            else:
                self.overlay.update_status(attempt, self.spin_max_attempts.value(), stat_name, val, min_val, "rolling")
        elif "error" in stats:
            self.overlay.update_status(attempt, self.spin_max_attempts.value(), "", stats["error"], "", "error")

    def on_reroll_finished(self, result: dict):
        self.btn_start_reroll.setEnabled(True)
        self.btn_stop_reroll.setEnabled(False)
        
        if result.get("success"):
            self.lbl_reroll_status.setText("✅ ITEM ENCONTRADO! Reroll Parado.")
            self.lbl_reroll_status.setStyleSheet("font-weight: bold; color: green;")
            
            QApplication.beep()
            
            found = result.get("found_stats", {})
            msg = "Item encontrado com sucesso!\n\nStats:"
            
            stat_name = ""
            val = ""
            for k, v in found.items():
                msg += f"\n- {k}: {v.get('value_found')}"
                if not stat_name:
                    stat_name = k
                    val = v.get('value_found')
                    
            self.overlay.update_status(result.get("attempts", 0), self.spin_max_attempts.value(), stat_name, val, "", "approved")
            
            # O overlay não sumirá automaticamente no sucesso
            # para que a mensagem fique no meio da tela
                
            QMessageBox.information(self, "Sucesso", msg)
        else:
            self.lbl_reroll_status.setText("❌ Reroll Finalizado ou Parado sem sucesso.")
            self.lbl_reroll_status.setStyleSheet("font-weight: bold; color: red;")
            
            state = "cancelled" if result.get("attempts", 0) < self.spin_max_attempts.value() else "error"
            self.overlay.update_status(result.get("attempts", 0), self.spin_max_attempts.value(), "", "", "", state)
            QTimer.singleShot(3000, self.overlay.hide)
            
            if result.get("attempts", 0) >= self.spin_max_attempts.value():
                QMessageBox.warning(self, "Limite Atingido", "Limite máximo de tentativas atingido.")

    def on_reroll_error(self, err_msg: str):
        self.btn_start_reroll.setEnabled(True)
        self.btn_stop_reroll.setEnabled(False)
        self.lbl_reroll_status.setText("ERRO!")
        self.overlay.update_status(self.progress_bar.value(), self.spin_max_attempts.value(), "", err_msg, "", "error")
        QTimer.singleShot(3000, self.overlay.hide)
        QMessageBox.critical(self, "Erro de Execução", f"Ocorreu um erro no Reroll Engine:\n{err_msg}")

    def show_guide(self):
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QScrollArea, QDialogButtonBox
        from PyQt6.QtGui import QPixmap
        from PyQt6.QtCore import Qt
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Manual do Usuário Avançado")
        dialog.resize(750, 650)
        
        layout = QVBoxLayout(dialog)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        guide_text = """
        <h3 style='color: #0088cc;'>Guia Prático: Como usar o Ark Omega Reroll</h3>
        <p>Siga estes passos para configurar e iniciar o bot de forma inteligente e sem bugs:</p>
        
        <b>1. Preparando o Item no Jogo</b><br>
        • Abra a <i>Imbue Station</i>.<br>
        • Coloque a Sela ou Armadura no <b>PRIMEIRO SLOT</b> do inventário da mesa.<br>
        • Faça pelo menos UM Imbue <b>manualmente</b> antes de iniciar o bot.<br><br>
        
        <b>2. Calibrando a Área do OCR (A Grande Sacada)</b><br>
        O tooltip é flutuante e some se você tirar o mouse do item. Por isso, <b>NÃO</b> tente capturar apenas a caixinha preta! Você deve capturar toda a extensão da mesa e o espaço lateral vazio onde a caixa costuma aparecer. Faça o seguinte:<br>
        • <b>[F11] Sup. Esq. Área OCR:</b> Coloque o mouse lá em cima, no canto superior esquerdo de toda a área de inventário da mesa (perto da palavra "INVENTÁRIO") e aperte F11.<br>
        • <b>[F12] Inf. Dir. Área OCR:</b> Mova o mouse bem lá para o fundo à direita e para baixo, cobrindo o espaço VAZIO. <i>(Não tem problema nenhum o tooltip sumir enquanto você arrasta o mouse para apertar F12! A coordenada será salva de qualquer jeito).</i><br><br>
        <i>Abaixo há um exemplo de como a sua área mental do OCR deve ser configurada (O quadrado vermelho ilustra o espaço capturado entre F11 e F12):</i>
        """
        
        lbl_text1 = QLabel(guide_text)
        lbl_text1.setWordWrap(True)
        lbl_text1.setStyleSheet("font-size: 13px;")
        content_layout.addWidget(lbl_text1)
        
        lbl_img = QLabel()
        lbl_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = QPixmap("exemplo_ocr.png")
        if not pixmap.isNull():
            lbl_img.setPixmap(pixmap.scaled(650, 650, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            lbl_img.setText("[ Salve a print que demonstra a área inteira vermelha como 'exemplo_ocr.png' na pasta do bot ]")
            lbl_img.setStyleSheet("color: red; font-weight: bold; padding: 20px; border: 1px dashed red;")
        content_layout.addWidget(lbl_img)
        
        guide_text2 = """
        <br><b>3. Posições de Clique (Ficam FORA do OCR)</b><br>
        Lembre-se: O botão de Reroll NÃO precisa e não deve estar dentro do quadrado vermelho do OCR!<br>
        • <b>[F10] Posição do Item:</b> Volte o mouse para cima do item no primeiro slot e aperte F10.<br>
        • <b>[F8] Botão REROLL:</b> Coloque o mouse EM CIMA do botão de Imbue/Upgrade e aperte F8.<br><br>
        
        <b>4. Iniciando</b><br>
        • Marque as caixinhas dos atributos desejados e aperte <b>F6</b> dentro do jogo.<br>
        • <i>Se der algo errado, aperte <b>HOME</b> a qualquer momento para parar.</i>
        """
        lbl_text2 = QLabel(guide_text2)
        lbl_text2.setWordWrap(True)
        lbl_text2.setStyleSheet("font-size: 13px;")
        content_layout.addWidget(lbl_text2)
        
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)
        
        dialog.exec()
