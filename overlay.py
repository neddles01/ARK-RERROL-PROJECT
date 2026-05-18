from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QProgressBar, QApplication, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

class OverlayWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        # Flags para tornar a janela um overlay invisível aos cliques
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowTransparentForInput |
            Qt.WindowType.ToolTip  # ToolTip geralmente ignora a minimização da janela pai
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.setup_ui()
        self.position_window()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Frame principal com fundo semi-transparente e borda
        self.frame = QFrame()
        self.frame.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 180);
                border-radius: 10px;
                border: 1px solid #00d2ff;
            }
        """)
        
        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(15, 15, 15, 15)
        
        # Header (Título e Botão X)
        header_layout = QHBoxLayout()
        self.lbl_title = QLabel("🔄 ARK Reroll")
        self.lbl_title.setStyleSheet("color: white; font-weight: bold; border: none; background: transparent;")
        
        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(20, 20)
        self.btn_close.setStyleSheet("""
            QPushButton {
                color: gray;
                border: none;
                background: transparent;
                font-weight: bold;
            }
        """)
        # Nota: O botão X não será clicável devido ao WindowTransparentForInput, 
        # mas está aqui visualmente conforme solicitado.
        
        header_layout.addWidget(self.lbl_title)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_close)
        
        frame_layout.addLayout(header_layout)
        
        # Status
        self.lbl_status = QLabel("Aguardando...")
        self.lbl_status.setStyleSheet("color: #ffb74d; font-weight: bold; font-size: 14px; border: none; background: transparent;")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_layout.addWidget(self.lbl_status)
        
        # Último valor encontrado
        self.lbl_detail = QLabel("Nenhum item lido ainda")
        self.lbl_detail.setStyleSheet("color: #cccccc; border: none; background: transparent;")
        self.lbl_detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_detail.setWordWrap(True)
        frame_layout.addWidget(self.lbl_detail)
        
        # Progresso
        self.progress = QProgressBar()
        self.progress.setFixedHeight(10)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: rgba(255, 255, 255, 30);
                border-radius: 5px;
            }
            QProgressBar::chunk {
                background-color: #00d2ff;
                border-radius: 5px;
            }
        """)
        frame_layout.addWidget(self.progress)
        
        # Atalhos
        self.lbl_hotkeys = QLabel("HOME: Parar Reroll")
        self.lbl_hotkeys.setStyleSheet("color: #888888; font-size: 10px; border: none; background: transparent;")
        self.lbl_hotkeys.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_layout.addWidget(self.lbl_hotkeys)
        
        main_layout.addWidget(self.frame)
        self.resize(300, 150)
        
    def position_window(self):
        screen = QApplication.primaryScreen()
        if screen:
            screen_geom = screen.geometry()
            # Usar 300 como fallback se self.width() ainda não estiver renderizado
            w = self.width() if self.width() > 100 else 300
            x = screen_geom.width() - w - 20
            y = 20
            self.move(x, y)
            
    def center_window(self):
        screen = QApplication.primaryScreen()
        if screen:
            screen_geom = screen.geometry()
            w = self.width() if self.width() > 100 else 400
            h = self.height() if self.height() > 100 else 200
            x = (screen_geom.width() - w) // 2
            y = (screen_geom.height() - h) // 2
            self.move(x, y)

    def update_status(self, attempt, max_attempts, stat_name, current_value, min_value, state):
        self.progress.setMaximum(max_attempts)
        self.progress.setValue(attempt)
        
        # Resetar o frame para o padrão (preto com borda azul)
        self.frame.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 180);
                border-radius: 10px;
                border: 1px solid #00d2ff;
            }
        """)
        
        if state == "rolling":
            self.lbl_status.setText(f"EM ANDAMENTO ({attempt}/{max_attempts})")
            self.lbl_status.setStyleSheet("color: #ffb74d; font-weight: bold; font-size: 14px; border: none; background: transparent;")
            self.lbl_detail.setText(f"{stat_name}: {current_value} (min: {min_value})")
            self.lbl_detail.setStyleSheet("color: #cccccc; font-size: 12px; border: none; background: transparent;")
        
        elif state == "not_found":
            self.lbl_status.setText(f"EM ANDAMENTO ({attempt}/{max_attempts})")
            self.lbl_status.setStyleSheet("color: #ffb74d; font-weight: bold; font-size: 14px; border: none; background: transparent;")
            self.lbl_detail.setText("Stat não apareceu")
            self.lbl_detail.setStyleSheet("color: #ef5350; font-size: 12px; border: none; background: transparent;")
            
        elif state == "approved":
            # Estilo de Sucesso Gigante
            self.frame.setStyleSheet("""
                QFrame {
                    background-color: rgba(0, 40, 0, 220);
                    border-radius: 15px;
                    border: 2px solid #00e676;
                }
            """)
            self.lbl_status.setText("🏆 SUCESSO!")
            self.lbl_status.setStyleSheet("color: #00e676; font-weight: bold; font-size: 26px; border: none; background: transparent;")
            self.lbl_detail.setText(f"Status [{stat_name}: {current_value}] atingido com sucesso!")
            self.lbl_detail.setStyleSheet("color: #b9f6ca; font-size: 16px; font-weight: bold; border: none; background: transparent;")
            self.center_window()
            
        elif state == "cancelled":
            self.lbl_status.setText("⏹ CANCELADO")
            self.lbl_status.setStyleSheet("color: #ef5350; font-weight: bold; font-size: 14px; border: none; background: transparent;")
            self.lbl_detail.setText("Processo interrompido pelo usuário.")
            self.lbl_detail.setStyleSheet("color: #cccccc; border: none; background: transparent;")
            
        elif state == "error":
            self.lbl_status.setText("❌ ERRO")
            self.lbl_status.setStyleSheet("color: #ef5350; font-weight: bold; font-size: 14px; border: none; background: transparent;")
            self.lbl_detail.setText(f"Falha: {current_value}") # Em caso de erro, passamos a msg no current_value
            self.lbl_detail.setStyleSheet("color: #ef5350; border: none; background: transparent;")
