import json
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, 
    QHeaderView, QDesktopWidget, QTabWidget
)
from config import ARQUIVO_CLIENTES

def carregar_clientes():
    if os.path.exists(ARQUIVO_CLIENTES):
        try:
            with open(ARQUIVO_CLIENTES, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def salvar_clientes(clientes):
    os.makedirs(os.path.dirname(ARQUIVO_CLIENTES), exist_ok=True)
    with open(ARQUIVO_CLIENTES, "w", encoding="utf-8") as f:
        json.dump(clientes, f, indent=4, ensure_ascii=False)

class TelaClientes(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestão de Clientes")
        self.ajustar_resolucao()
        
        self.clientes = carregar_clientes()
        self.cliente_em_edicao = None

        # Layout Principal com Abas
        layout_principal = QVBoxLayout()
        self.abas = QTabWidget()
        
        self.aba_listagem = QWidget()
        self.aba_cadastro = QWidget()
        self.aba_edicao = QWidget()

        self.inicializar_aba_listagem()
        self.inicializar_aba_cadastro()
        self.inicializar_aba_edicao()

        self.abas.addTab(self.aba_listagem, "Clientes Cadastrados")
        self.abas.addTab(self.aba_cadastro, "Novo Cliente")

        layout_principal.addWidget(self.abas)
        self.setLayout(layout_principal)

    def ajustar_resolucao(self):
        tela = QDesktopWidget().screenGeometry()
        largura = int(tela.width() * 0.8)
        altura = int(tela.height() * 0.8)
        pos_x = int((tela.width() - largura) / 2)
        pos_y = int((tela.height() - altura) / 2)
        self.setGeometry(pos_x, pos_y, largura, altura)

    # --- ABA 1: LISTAGEM ---
    def inicializar_aba_listagem(self):
        layout = QVBoxLayout()

        self.tabela = QTableWidget()
        self.tabela.setColumnCount(10)
        self.tabela.setHorizontalHeaderLabels(
            ["Nome", "CPF/CNPJ", "Email", "Telefone", "Endereço", "Nº", "Bairro", "Cidade", "Estado", "IE"]
        )
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.setSelectionMode(QTableWidget.SingleSelection)
        
        header = self.tabela.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)

        layout.addWidget(self.tabela)

        btn_layout = QHBoxLayout()
        btn_editar = QPushButton("Editar Selecionado")
        btn_editar.setStyleSheet("background-color: #f0ad4e; color: white; font-weight: bold;")
        btn_editar.clicked.connect(self.preparar_edicao)
        
        btn_excluir = QPushButton("Excluir Selecionado")
        btn_excluir.setStyleSheet("background-color: #d9534f; color: white; font-weight: bold;")
        btn_excluir.clicked.connect(self.excluir_cliente)
        
        btn_layout.addWidget(btn_editar)
        btn_layout.addWidget(btn_excluir)
        layout.addLayout(btn_layout)

        self.aba_listagem.setLayout(layout)
        self.atualizar_tabela()

    def atualizar_tabela(self):
        self.tabela.setRowCount(0)
        for row, c in enumerate(self.clientes):
            self.tabela.insertRow(row)
            self.tabela.setItem(row, 0, QTableWidgetItem(c.get("nome", "")))
            self.tabela.setItem(row, 1, QTableWidgetItem(c.get("cpf_cnpj", "")))
            self.tabela.setItem(row, 2, QTableWidgetItem(c.get("email", "")))
            self.tabela.setItem(row, 3, QTableWidgetItem(c.get("telefone", "")))
            self.tabela.setItem(row, 4, QTableWidgetItem(c.get("endereco", "")))
            self.tabela.setItem(row, 5, QTableWidgetItem(c.get("numero", "")))
            self.tabela.setItem(row, 6, QTableWidgetItem(c.get("bairro", "")))
            self.tabela.setItem(row, 7, QTableWidgetItem(c.get("cidade", "")))
            self.tabela.setItem(row, 8, QTableWidgetItem(c.get("estado", "")))
            self.tabela.setItem(row, 9, QTableWidgetItem(c.get("ie", "")))

    # --- ABA 2: CADASTRO ---
    def inicializar_aba_cadastro(self):
        layout = QVBoxLayout()
        self.inputs_cad = self.criar_formulario(layout)
        
        btn_salvar = QPushButton("Salvar Cliente")
        btn_salvar.setStyleSheet("background-color: #5cb85c; color: white; font-weight: bold; height: 40px;")
        btn_salvar.clicked.connect(self.salvar_novo_cliente)
        layout.addWidget(btn_salvar)
        layout.addStretch()
        self.aba_cadastro.setLayout(layout)

    # --- ABA 3: EDIÇÃO ---
    def inicializar_aba_edicao(self):
        layout = QVBoxLayout()
        self.inputs_edit = self.criar_formulario(layout)
        
        btn_salvar = QPushButton("Salvar Alterações")
        btn_salvar.setStyleSheet("background-color: #0275d8; color: white; font-weight: bold; height: 40px;")
        btn_salvar.clicked.connect(self.confirmar_edicao)
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(lambda: self.abas.removeTab(self.abas.indexOf(self.aba_edicao)))

        layout.addWidget(btn_salvar)
        layout.addWidget(btn_cancelar)
        layout.addStretch()
        self.aba_edicao.setLayout(layout)

    def criar_formulario(self, layout_pai):
        """Cria os campos do formulário para evitar repetição de código"""
        dicio_inputs = {}
        campos = [
            ("nome", "Nome:"), ("cpf_cnpj", "CPF/CNPJ:"), ("email", "Email:"),
            ("telefone", "Telefone:"), ("endereco", "Rua/Endereço:"), ("numero", "Número:"),
            ("bairro", "Bairro:"), ("cidade", "Cidade:"), ("estado", "Estado:"), ("ie", "Inscrição Estadual:")
        ]
        
        for chave, label in campos:
            layout_pai.addWidget(QLabel(label))
            edit = QLineEdit()
            layout_pai.addWidget(edit)
            dicio_inputs[chave] = edit
            
        return dicio_inputs

    def salvar_novo_cliente(self):
        novo_c = {chave: input.text().strip() for chave, input in self.inputs_cad.items()}
        
        if not novo_c["nome"] or not novo_c["cpf_cnpj"]:
            QMessageBox.warning(self, "Erro", "Nome e CPF/CNPJ são obrigatórios!")
            return

        self.clientes.append(novo_c)
        salvar_clientes(self.clientes)
        QMessageBox.information(self, "Sucesso", "Cliente cadastrado!")
        
        for input in self.inputs_cad.values(): input.clear()
        self.atualizar_tabela()
        self.abas.setCurrentWidget(self.aba_listagem)

    def preparar_edicao(self):
        row = self.tabela.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Erro", "Selecione um cliente!")
            return

        self.cliente_em_edicao = row
        cliente = self.clientes[row]

        for chave, input_field in self.inputs_edit.items():
            input_field.setText(cliente.get(chave, ""))

        if self.abas.indexOf(self.aba_edicao) == -1:
            self.abas.addTab(self.aba_edicao, "Editar Cliente")
        self.abas.setCurrentWidget(self.aba_edicao)

    def confirmar_edicao(self):
        dados_atualizados = {chave: input.text().strip() for chave, input in self.inputs_edit.items()}
        
        self.clientes[self.cliente_em_edicao] = dados_atualizados
        salvar_clientes(self.clientes)
        
        self.atualizar_tabela()
        self.abas.removeTab(self.abas.indexOf(self.aba_edicao))
        self.abas.setCurrentWidget(self.aba_listagem)
        QMessageBox.information(self, "Sucesso", "Dados atualizados!")

    def excluir_cliente(self):
        row = self.tabela.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Erro", "Selecione um cliente!")
            return

        if QMessageBox.question(self, "Excluir", "Deseja excluir?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            self.clientes.pop(row)
            salvar_clientes(self.clientes)
            self.atualizar_tabela()
