import json
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QTabWidget, QDesktopWidget, QHeaderView, QFrame
)
from PyQt5.QtCore import Qt
from config import ARQUIVO_ACESSORIOS

# Novo arquivo de configuração para o preço do KG (certifique-se que exista no config.py ou use o caminho abaixo)
ARQUIVO_PRECO_KG = os.path.join(os.path.dirname(ARQUIVO_ACESSORIOS), "preco_aluminio.json")

def carregar_acessorios():
    if os.path.exists(ARQUIVO_ACESSORIOS):
        try:
            with open(ARQUIVO_ACESSORIOS, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def salvar_acessorios(acessorios):
    os.makedirs(os.path.dirname(ARQUIVO_ACESSORIOS), exist_ok=True)
    with open(ARQUIVO_ACESSORIOS, "w", encoding="utf-8") as f:
        json.dump(acessorios, f, indent=4, ensure_ascii=False)

def carregar_preco_kg():
    if os.path.exists(ARQUIVO_PRECO_KG):
        try:
            with open(ARQUIVO_PRECO_KG, "r", encoding="utf-8") as f:
                return json.load(f).get("preco_kg", 0.0)
        except: return 0.0
    return 0.0

def salvar_preco_kg(valor):
    with open(ARQUIVO_PRECO_KG, "w", encoding="utf-8") as f:
        json.dump({"preco_kg": valor}, f, indent=4)

class TelaAcessorios(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cadastro de Perfis e Itens")
        self.definir_resolucao()

        self.acessorios = carregar_acessorios()
        self.acessorio_em_edicao = None

        self.layout_principal = QVBoxLayout()
        self.abas = QTabWidget()
        
        # Abas
        self.aba_listagem = QWidget()
        self.aba_cadastro = QWidget()
        self.aba_edicao = QWidget()
        self.aba_preco_aluminio = QWidget() # Nova Aba

        self.inicializar_aba_listagem()
        self.inicializar_aba_cadastro()
        self.inicializar_aba_edicao()
        self.inicializar_aba_preco_kg() # Inicializa nova aba

        self.abas.addTab(self.aba_listagem, "Itens Cadastrados")
        self.abas.addTab(self.aba_cadastro, "Cadastrar Novo Item")
        self.abas.addTab(self.aba_preco_aluminio, "Preço Alumínio/kg")

        self.layout_principal.addWidget(self.abas)
        self.setLayout(self.layout_principal)

    def definir_resolucao(self):
        tela = QDesktopWidget().screenGeometry()
        largura, altura = int(tela.width() * 0.8), int(tela.height() * 0.8)
        pos_x, pos_y = int((tela.width() - largura) / 2), int((tela.height() - altura) / 2)
        self.setGeometry(pos_x, pos_y, largura, altura)

    def inicializar_aba_listagem(self):
        layout = QVBoxLayout()
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(3)
        self.tabela.setHorizontalHeaderLabels(["Código", "Nome/Descrição", "Peso (kg)"])
        
        header = self.tabela.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Interactive)
        
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.tabela)

        btn_edit = QPushButton("Editar Item Selecionado")
        btn_edit.setStyleSheet("background-color: #f0ad4e; color: white; font-weight: bold;")
        btn_edit.clicked.connect(self.editar_acessorio)
        layout.addWidget(btn_edit)

        btn_exc = QPushButton("Excluir Item Selecionado")
        btn_exc.setStyleSheet("background-color: #d9534f; color: white; font-weight: bold;")
        btn_exc.clicked.connect(self.excluir_acessorio)
        layout.addWidget(btn_exc)

        self.aba_listagem.setLayout(layout)
        self.atualizar_tabela()

    def atualizar_tabela(self):
        self.tabela.setRowCount(0)
        for row, item in enumerate(self.acessorios):
            self.tabela.insertRow(row)
            self.tabela.setItem(row, 0, QTableWidgetItem(str(item["codigo"])))
            self.tabela.setItem(row, 1, QTableWidgetItem(item["nome"]))
            self.tabela.setItem(row, 2, QTableWidgetItem(f"{float(item.get('peso', 0)):.3f} kg"))

    def inicializar_aba_cadastro(self):
        layout = QVBoxLayout()
        self.input_codigo = QLineEdit()
        self.input_nome = QLineEdit()
        self.input_peso = QLineEdit() # Alterado de valor para peso

        layout.addWidget(QLabel("Código do Item:"))
        layout.addWidget(self.input_codigo)
        layout.addWidget(QLabel("Descrição (ex: Trilho Superior Suprema):"))
        layout.addWidget(self.input_nome)
        layout.addWidget(QLabel("Peso do Perfil (kg por peça/barra):"))
        layout.addWidget(self.input_peso)

        btn_salvar = QPushButton("Salvar Item")
        btn_salvar.setStyleSheet("background-color: #5cb85c; color: white; font-weight: bold;")
        btn_salvar.clicked.connect(self.salvar_novo_acessorio)
        layout.addWidget(btn_salvar)
        layout.addStretch()
        self.aba_cadastro.setLayout(layout)

    def salvar_novo_acessorio(self):
        codigo, nome, peso_str = self.input_codigo.text().strip(), self.input_nome.text().strip(), self.input_peso.text().replace(',', '.').strip()
        if not codigo or not nome or not peso_str:
            QMessageBox.warning(self, "Erro", "Preencha todos os campos!")
            return
        try:
            peso = float(peso_str)
        except:
            QMessageBox.warning(self, "Erro", "Peso inválido!")
            return

        self.acessorios.append({"codigo": codigo, "nome": nome, "peso": peso})
        salvar_acessorios(self.acessorios)
        QMessageBox.information(self, "Sucesso", "Item cadastrado com sucesso!")
        self.input_codigo.clear(); self.input_nome.clear(); self.input_peso.clear()
        self.atualizar_tabela()
        self.abas.setCurrentWidget(self.aba_listagem)

    def inicializar_aba_preco_kg(self):
        """Nova aba para definir o valor do Alumínio KG"""
        layout = QVBoxLayout()
        
        frame = QFrame()
        frame.setStyleSheet("background-color: #f4f4f4; border: 1px solid #ccc; border-radius: 5px;")
        f_layout = QVBoxLayout(frame)
        
        f_layout.addWidget(QLabel("<b>Defina o valor atual do KG do Alumínio (R$):</b>"))
        self.input_global_kg = QLineEdit()
        self.input_global_kg.setText(str(carregar_preco_kg()).replace('.', ','))
        self.input_global_kg.setStyleSheet("font-size: 18px; padding: 10px;")
        f_layout.addWidget(self.input_global_kg)
        
        btn_atualizar = QPushButton("Atualizar Preço do KG")
        btn_atualizar.setStyleSheet("background-color: #0275d8; color: white; font-weight: bold; height: 40px;")
        btn_atualizar.clicked.connect(self.atualizar_preco_kg_global)
        f_layout.addWidget(btn_atualizar)
        
        layout.addWidget(frame)
        layout.addStretch()
        self.aba_preco_aluminio.setLayout(layout)

    def atualizar_preco_kg_global(self):
        try:
            novo_preco = float(self.input_global_kg.text().replace(',', '.'))
            salvar_preco_kg(novo_preco)
            QMessageBox.information(self, "Sucesso", f"Preço do alumínio atualizado para R$ {novo_preco:.2f}/kg")
        except:
            QMessageBox.warning(self, "Erro", "Digite um valor numérico válido!")

    def inicializar_aba_edicao(self):
        layout = QVBoxLayout()
        self.edit_codigo, self.edit_nome, self.edit_peso = QLineEdit(), QLineEdit(), QLineEdit()

        layout.addWidget(QLabel("Código do Item:"))
        layout.addWidget(self.edit_codigo)
        layout.addWidget(QLabel("Nome:"))
        layout.addWidget(self.edit_nome)
        layout.addWidget(QLabel("Peso (kg):"))
        layout.addWidget(self.edit_peso)

        btn_salvar = QPushButton("Salvar Alterações")
        btn_salvar.setStyleSheet("background-color: #0275d8; color: white; font-weight: bold;")
        btn_salvar.clicked.connect(self.salvar_edicao)
        layout.addWidget(btn_salvar)
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(lambda: self.abas.removeTab(self.abas.indexOf(self.aba_edicao)))
        layout.addWidget(btn_cancelar)
        layout.addStretch()
        self.aba_edicao.setLayout(layout)

    def editar_acessorio(self):
        row = self.tabela.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Erro", "Selecione um Item!")
            return
        self.acessorio_em_edicao = row
        item = self.acessorios[row]
        self.edit_codigo.setText(str(item["codigo"]))
        self.edit_nome.setText(item["nome"])
        self.edit_peso.setText(str(item.get("peso", 0)))
        if self.abas.indexOf(self.aba_edicao) == -1:
            self.abas.addTab(self.aba_edicao, "Editar Item")
        self.abas.setCurrentWidget(self.aba_edicao)

    def salvar_edicao(self):
        try:
            p = float(self.edit_peso.text().replace(',', '.'))
            self.acessorios[self.acessorio_em_edicao] = {
                "codigo": self.edit_codigo.text(),
                "nome": self.edit_nome.text(),
                "peso": p
            }
            salvar_acessorios(self.acessorios)
            self.atualizar_tabela()
            self.abas.removeTab(self.abas.indexOf(self.aba_edicao))
            QMessageBox.information(self, "Sucesso", "Item atualizado!")
        except: QMessageBox.warning(self, "Erro", "Peso inválido!")

    def excluir_acessorio(self):
        row = self.tabela.currentRow()
        if row >= 0 and QMessageBox.question(self, "Excluir", "Deseja excluir?") == QMessageBox.Yes:
            self.acessorios.pop(row)
            salvar_acessorios(self.acessorios)
            self.atualizar_tabela()
