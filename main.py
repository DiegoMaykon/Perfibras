import sys
import os
import shutil
import json
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication,QGridLayout,QMainWindow, QPushButton, QVBoxLayout, QDesktopWidget, QWidget,
    QHBoxLayout, QFileDialog, QMessageBox, QLabel)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer
from acessorios import TelaAcessorios
from pedidos import TelaPedidos
from config import PASTA_DADOS
from clientes import TelaClientes
from pathlib import Path

# ==============================
# 🔹 Função auxiliar para localizar imagens mesmo após empacotamento
# ==============================
def resource_path(relative_path):
    """Obtém o caminho absoluto para recursos, compatível com PyInstaller."""
    try:
        base_path = sys._MEIPASS  # Diretório temporário usado pelo PyInstaller
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Função para criar pasta de dados
# --------------------------
def criar_pasta_dados():
    """Cria a pasta 'dados' dentro do AppData/Roaming/NelsonRosa."""
    pasta_appdata = Path(os.getenv("APPDATA")) / "NelsonRosa" / "dados"
    pasta_appdata.mkdir(parents=True, exist_ok=True)
    print(f"Pasta de dados: {pasta_appdata}")  # Debug opcional
    return str(pasta_appdata)

# Caminho base de dados
PASTA_DADOS = criar_pasta_dados()

# Caminhos completos dos arquivos JSON
ARQUIVO_CLIENTES = os.path.join(PASTA_DADOS, "clientes.json")
ARQUIVO_ACESSORIOS = os.path.join(PASTA_DADOS, "acessorios.json")
ARQUIVO_PEDIDOS = os.path.join(PASTA_DADOS, "pedidos.json")

# Lista principal usada para backup
ARQUIVOS_SISTEMA = [ARQUIVO_CLIENTES, ARQUIVO_ACESSORIOS, ARQUIVO_PEDIDOS]

# Número máximo de backups a manter
MAX_BACKUPS = 1


# ==============================
# 🔹 Classe Principal com Layout de Cards
# ==============================
class TelaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Pedidos Perfibras - Nelson Rosa - V1.0")
        
        # Estilo Global (Fundo e Cards)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e2f; /* Fundo escuro moderno */
            }
            QPushButton {
                background-color: #2d2d44;
                color: white;
                font-size: 18px;
                font-weight: bold;
                border-radius: 20px;
                border: 2px solid #3d3d5c;
                min-width: 250px;
                min-height: 180px; /* Tamanho do Card */
            }
            QPushButton:hover {
                background-color: #3d3d5c;
                border: 2px solid #ff9d00; /* Cor de destaque ao passar o mouse */
                margin-top: -5px; /* Efeito de elevação */
            }
            QPushButton#btn_sair {
                background-color: #442d2d;
                border: 2px solid #5c3d3d;
            }
            QPushButton#btn_sair:hover {
                background-color: #ff4444;
            }
            QLabel#titulo {
                color: white;
                font-size: 32px;
                font-weight: bold;
                margin-bottom: 20px;
            }
        """)

        self.inicializar_ui()
        self.inicializar_backup_automatico()
        self.ajustar_resolucao()

    def ajustar_resolucao(self):
        tela = QDesktopWidget().screenGeometry()
        self.setGeometry(0, 0, tela.width(), tela.height())

    def inicializar_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal vertical
        layout_v = QVBoxLayout()
        central_widget.setLayout(layout_v)

        # Título do Sistema
        lbl_titulo = QLabel("GESTÃO DE PEDIDOS NELSON ROSA - PERFIBRAS")
        lbl_titulo.setObjectName("titulo")
        lbl_titulo.setAlignment(Qt.AlignCenter)
        layout_v.addWidget(lbl_titulo)

        # Grade de Cards (2 colunas)
        grid_layout = QGridLayout()
        grid_layout.setSpacing(30) # Espaço entre os cards

        # Criar os botões (Cards)
        self.btn_clientes = QPushButton("👤\n\nCLIENTES")
        self.btn_acessorios = QPushButton("📦\n\nITENS / ESTOQUE")
        self.btn_pedidos = QPushButton("📝\n\nNOVO PEDIDO")
        self.btn_backup = QPushButton("💾\n\nGERAR BACKUP")
        self.btn_restaurar = QPushButton("🔄\n\nRESTAURAR DADOS")
        self.btn_sair = QPushButton("🚪\n\nSAIR")
        self.btn_sair.setObjectName("btn_sair")

        # Adicionar à grade (linha, coluna)
        grid_layout.addWidget(self.btn_clientes, 0, 0)
        grid_layout.addWidget(self.btn_acessorios, 0, 1)
        grid_layout.addWidget(self.btn_pedidos, 1, 0)
        grid_layout.addWidget(self.btn_backup, 1, 1)
        grid_layout.addWidget(self.btn_restaurar, 2, 0)
        grid_layout.addWidget(self.btn_sair, 2, 1)

        # Centralizar a grade na tela
        container_grid = QHBoxLayout()
        container_grid.addStretch()
        container_grid.addLayout(grid_layout)
        container_grid.addStretch()

        layout_v.addStretch()
        layout_v.addLayout(container_grid)
        layout_v.addStretch()

        # Conectar botões
        self.btn_clientes.clicked.connect(self.abrir_clientes)
        self.btn_acessorios.clicked.connect(self.abrir_acessorios)
        self.btn_pedidos.clicked.connect(self.abrir_pedidos)
        self.btn_backup.clicked.connect(self.fazer_backup)
        self.btn_restaurar.clicked.connect(self.restaurar_backup)
        self.btn_sair.clicked.connect(self.close)

    # ==============================
    # Fundo dinâmico
    # ==============================
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.atualizar_fundo()

    def atualizar_fundo(self):
        """Faz o fundo preencher toda a tela (sem bordas)"""
        if hasattr(self, "pixmap_original"):
            scaled_pixmap = self.pixmap_original.scaled(
                self.size(),
                Qt.IgnoreAspectRatio,
                Qt.SmoothTransformation
            )
            self.label_fundo.setPixmap(scaled_pixmap)
            self.label_fundo.resize(self.size())

    # ==============================
    # Telas
    # ==============================
    def abrir_clientes(self):
        self.tela_clientes = TelaClientes()
        self.tela_clientes.show()

    def abrir_acessorios(self):
        self.tela_acessorios = TelaAcessorios()
        self.tela_acessorios.show()

    def abrir_pedidos(self):
        self.tela_pedidos = TelaPedidos()
        self.tela_pedidos.show()

    # ==============================
    # Backup manual
    # ==============================
    def fazer_backup(self):
        pasta_backup = QFileDialog.getExistingDirectory(self, "Selecionar Pasta de Backup")
        if not pasta_backup:
            return
        self.realizar_backup(pasta_backup)
        QMessageBox.information(self, "Backup Concluído", f"Backup realizado com sucesso em:\n{pasta_backup}")

    # ==============================
    # Restauração manual
    # ==============================
    def restaurar_backup(self):
        pasta_backup = QFileDialog.getExistingDirectory(self, "Selecionar Pasta do Backup")
        if not pasta_backup:
            return
        confirm = QMessageBox.question(
            self,
            "Confirmar Restauração",
            "Deseja realmente restaurar este backup? Isso irá substituir os arquivos atuais.",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return
        for arquivo in ARQUIVOS_SISTEMA:
            nome = os.path.basename(arquivo)
            arquivo_backup = os.path.join(pasta_backup, nome)
            if os.path.exists(arquivo_backup):
                shutil.copy2(arquivo_backup, arquivo)
        QMessageBox.information(self, "Restauração Concluída", "Backup restaurado com sucesso!\nReinicie o sistema para atualizar as telas.")

    # ==============================
    # Backup automático diário
    # ==============================
    def inicializar_backup_automatico(self):
        self.pasta_backup_automatica = os.path.join(PASTA_DADOS, "backups")
        os.makedirs(self.pasta_backup_automatica, exist_ok=True)
        self.backup_automatico()
        self.timer_backup = QTimer()
        self.timer_backup.timeout.connect(self.backup_automatico)
        self.timer_backup.start(24 * 60 * 60 * 1000)  # 1 dia

    def backup_automatico(self):
        self.realizar_backup(self.pasta_backup_automatica, mostrar_msg=False)
        self.limpar_backups_antigos(self.pasta_backup_automatica)
        print(f"Backup automático realizado em: {self.pasta_backup_automatica}")

    # ==============================
    # Funções de backup
    # ==============================
    def realizar_backup(self, pasta_backup, mostrar_msg=True):
        os.makedirs(pasta_backup, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pasta_destino = os.path.join(pasta_backup, f"backup_{timestamp}")
        os.makedirs(pasta_destino, exist_ok=True)
        for arquivo in ARQUIVOS_SISTEMA:
            if os.path.exists(arquivo):
                shutil.copy2(arquivo, pasta_destino)
        if mostrar_msg:
            print(f"Backup realizado em: {pasta_destino}")

    def limpar_backups_antigos(self, pasta_backup):
        if not os.path.exists(pasta_backup):
            return
        backups = [d for d in os.listdir(pasta_backup) if os.path.isdir(os.path.join(pasta_backup, d))]
        backups.sort()
        while len(backups) > MAX_BACKUPS:
            antigo = backups.pop(0)
            caminho_antigo = os.path.join(pasta_backup, antigo)
            shutil.rmtree(caminho_antigo)
            print(f"Backup antigo removido: {caminho_antigo}")

# ==============================
# Execução
# ==============================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = TelaPrincipal()
    janela.show()
    sys.exit(app.exec_())
