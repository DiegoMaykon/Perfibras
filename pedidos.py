import json
import os
import sys
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
    QTabWidget, QCompleter, QHeaderView, QDesktopWidget, QFileDialog, QFrame
)
from PyQt5.QtCore import Qt
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

from config import ARQUIVO_CLIENTES, ARQUIVO_ACESSORIOS, ARQUIVO_PEDIDOS

# Caminho para o preço do KG
ARQUIVO_PRECO_KG = os.path.join(os.path.dirname(ARQUIVO_ACESSORIOS), "preco_aluminio.json")

# --- Funções de Persistência ---
def carregar_json(arquivo):
    if os.path.exists(arquivo):
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return []
    return []

def salvar_json(dados, arquivo):
    os.makedirs(os.path.dirname(arquivo), exist_ok=True)
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def carregar_valor_kg_atual():
    if os.path.exists(ARQUIVO_PRECO_KG):
        try:
            with open(ARQUIVO_PRECO_KG, "r", encoding="utf-8") as f:
                return float(json.load(f).get("preco_kg", 0.0))
        except: return 0.0
    return 0.0

class TelaPedidos(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Gestão Comercial - Iorli Representações (2026)")
        self.ajustar_resolucao()

        self.pedidos = carregar_json(ARQUIVO_PEDIDOS)
        self.clientes = carregar_json(ARQUIVO_CLIENTES)
        self.acessorios = carregar_json(ARQUIVO_ACESSORIOS)
        self.itens_pedido_atual = []
        self.pedido_em_edicao_index = None 

        self.inicializar_ui()

    def ajustar_resolucao(self):
        tela = QDesktopWidget().screenGeometry()
        largura, altura = int(tela.width() * 0.8), int(tela.height() * 0.8)
        pos_x, pos_y = int((tela.width() - largura) / 2), int((tela.height() - altura) / 2)
        self.setGeometry(pos_x, pos_y, largura, altura)

    def inicializar_ui(self):
        layout_principal = QVBoxLayout(self)
        self.abas = QTabWidget()
        
        self.aba_novo = self.criar_aba_novo_pedido()
        self.aba_lista = self.criar_aba_pesquisar()

        self.abas.addTab(self.aba_novo, "📝 Gerar Nova Proposta")
        self.abas.addTab(self.aba_lista, "🔍 Histórico / Pesquisa")
        
        layout_principal.addWidget(self.abas)

    def criar_aba_novo_pedido(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        frame_cli = QFrame()
        frame_cli.setFrameShape(QFrame.StyledPanel)
        frame_cli.setStyleSheet("background-color: #f9f9f9; border-radius: 5px;")
        layout_cli = QVBoxLayout(frame_cli)
        layout_cli.addWidget(QLabel("<b>SELECIONE O CLIENTE:</b>"))
        
        self.input_cliente = QLineEdit()
        nomes_cli = [c.get("nome", "") for c in self.clientes]
        self.input_cliente.setCompleter(QCompleter(nomes_cli))
        self.input_cliente.setStyleSheet("padding: 8px; background-color: white; border: 1px solid #ccc;")
        layout_cli.addWidget(self.input_cliente)
        layout.addWidget(frame_cli)

        frame_itens = QFrame()
        frame_itens.setFrameShape(QFrame.StyledPanel)
        layout_item = QVBoxLayout(frame_itens)
        layout_item.addWidget(QLabel("<b>ADICIONAR PERFIL PELO CÓDIGO:</b>"))
        
        h_box = QHBoxLayout()
        self.input_prod = QLineEdit()
        self.input_prod.setPlaceholderText("Digite o CÓDIGO do item...")
        
        # Completer agora usa o CÓDIGO
        codigos_acc = [str(a.get("codigo", "")) for a in self.acessorios]
        self.input_prod.setCompleter(QCompleter(codigos_acc))
        
        self.input_qtd = QLineEdit()
        self.input_qtd.setPlaceholderText("Qtd Peças")
        self.input_qtd.setFixedWidth(80)
        
        btn_add = QPushButton("➕ Adicionar")
        btn_add.setStyleSheet("background-color: #0275d8; color: white; font-weight: bold; padding: 6px;")
        btn_add.clicked.connect(self.adicionar_item)
        
        h_box.addWidget(self.input_prod, 4)
        h_box.addWidget(self.input_qtd, 1)
        h_box.addWidget(btn_add, 1)
        layout_item.addLayout(h_box)
        layout.addWidget(frame_itens)

        self.tabela_novo = QTableWidget(0, 6) # 6 colunas para incluir Código
        self.tabela_novo.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela_novo.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela_novo.setHorizontalHeaderLabels(["Código", "Item", "Peso Unit.", "Qtd", "Peso Total", "Subtotal"])
        self.tabela_novo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.tabela_novo)

        btn_remover = QPushButton("❌ Remover Item Selecionado")
        btn_remover.clicked.connect(self.remover_item_lista)
        layout.addWidget(btn_remover)

        rodape = QHBoxLayout()
        self.lbl_total = QLabel("TOTAL: R$ 0,00")
        self.lbl_total.setStyleSheet("font-size: 20px; font-weight: bold; color: #1e7e34;")
        
        self.btn_salvar = QPushButton("💾 SALVAR E GERAR PROPOSTA")
        self.btn_salvar.setFixedHeight(45)
        self.btn_salvar.setStyleSheet("background-color: #28a745; color: white; font-weight: bold;")
        self.btn_salvar.clicked.connect(self.finalizar_pedido)
        
        rodape.addWidget(self.lbl_total)
        rodape.addStretch()
        rodape.addWidget(self.btn_salvar)
        layout.addLayout(rodape)

        return widget

    def adicionar_item(self):
        codigo_buscado = self.input_prod.text().strip()
        qtd_s = self.input_qtd.text().replace(",", ".")
        
        # Busca o item pelo CÓDIGO
        item_obj = next((a for a in self.acessorios if str(a.get("codigo", "")) == codigo_buscado), None)
        
        preco_kg = carregar_valor_kg_atual()
        if preco_kg <= 0:
            QMessageBox.warning(self, "Aviso", "O preço do KG não foi definido em Acessórios!")
            return

        if item_obj and (qtd_s.replace(".", "", 1).isdigit()):
            qtd = float(qtd_s)
            peso_unit = float(item_obj.get("peso", 0))
            peso_total = peso_unit * qtd
            subtotal = peso_total * preco_kg

            self.itens_pedido_atual.append({
                "codigo": item_obj.get("codigo", ""),
                "nome": item_obj.get("nome", ""),
                "peso_unit": peso_unit,
                "qtd": qtd,
                "peso_total": peso_total,
                "subtotal": subtotal,
                "preco_kg_na_epoca": preco_kg
            })
            self.atualizar_tabela_novo()
            self.input_prod.clear(); self.input_qtd.clear(); self.input_prod.setFocus()
        else:
            QMessageBox.warning(self, "Aviso", "Código do item não encontrado ou quantidade inválida.")

    def remover_item_lista(self):
        linha = self.tabela_novo.currentRow()
        if linha >= 0:
            self.itens_pedido_atual.pop(linha)
            self.atualizar_tabela_novo()

    def atualizar_tabela_novo(self):
        self.tabela_novo.setRowCount(0)
        total = sum(i["subtotal"] for i in self.itens_pedido_atual)
        for i, item in enumerate(self.itens_pedido_atual):
            self.tabela_novo.insertRow(i)
            self.tabela_novo.setItem(i, 0, QTableWidgetItem(str(item["codigo"])))
            self.tabela_novo.setItem(i, 1, QTableWidgetItem(item["nome"]))
            self.tabela_novo.setItem(i, 2, QTableWidgetItem(f"{item['peso_unit']:.3f} kg"))
            self.tabela_novo.setItem(i, 3, QTableWidgetItem(str(item["qtd"])))
            self.tabela_novo.setItem(i, 4, QTableWidgetItem(f"{item['peso_total']:.3f} kg"))
            self.tabela_novo.setItem(i, 5, QTableWidgetItem(f"R$ {item['subtotal']:.2f}"))
        self.lbl_total.setText(f"TOTAL: R$ {total:.2f}")

    def finalizar_pedido(self):
        nome_cli = self.input_cliente.text()
        cliente = next((c for c in self.clientes if c["nome"] == nome_cli), None)

        if not cliente or not self.itens_pedido_atual:
            QMessageBox.warning(self, "Erro", "Selecione um cliente e itens.")
            return

        total_pedido = sum(i["subtotal"] for i in self.itens_pedido_atual)

        if self.pedido_em_edicao_index is not None:
            idx = self.pedido_em_edicao_index
            self.pedidos[idx].update({"cliente": cliente, "itens": self.itens_pedido_atual, "total": total_pedido})
            pedido_final = self.pedidos[idx]
            self.pedido_em_edicao_index = None
            self.btn_salvar.setText("💾 SALVAR E GERAR PROPOSTA")
        else:
            pedido_final = {
                "numero": len(self.pedidos) + 1001,
                "data": datetime.now().strftime("%d/%m/%Y"),
                "cliente": cliente, "itens": self.itens_pedido_atual, "total": total_pedido
            }
            self.pedidos.append(pedido_final)

        salvar_json(self.pedidos, ARQUIVO_PEDIDOS)
        self.gerar_pdf_pedido(pedido_final)
        self.itens_pedido_atual = []; self.input_cliente.clear(); self.atualizar_tabela_novo(); self.atualizar_hist()

    def criar_aba_pesquisar(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.input_busca = QLineEdit()
        self.input_busca.setPlaceholderText("🔍 Filtrar histórico por cliente...")
        self.input_busca.textChanged.connect(self.atualizar_hist)
        layout.addWidget(self.input_busca)

        self.tabela_hist = QTableWidget(0, 7)
        self.tabela_hist.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela_hist.setHorizontalHeaderLabels(["Nº", "Data", "Cliente", "Total", "PDF", "Editar", "Excluir"])
        self.tabela_hist.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.tabela_hist)
        self.atualizar_hist()
        return widget

    def atualizar_hist(self):
        busca = self.input_busca.text().lower()
        self.tabela_hist.setRowCount(0)
        
        for i, p in enumerate(self.pedidos):
            # --- CORREÇÃO AQUI ---
            # Verifica se 'cliente' é um dicionário ou apenas uma string
            cli_data = p.get("cliente", "")
            if isinstance(cli_data, dict):
                nome_cliente = cli_data.get("nome", "")
            else:
                nome_cliente = str(cli_data)
            # ---------------------

            if busca in nome_cliente.lower():
                row = self.tabela_hist.rowCount()
                self.tabela_hist.insertRow(row)
                self.tabela_hist.setItem(row, 0, QTableWidgetItem(p.get("data", "")))
                self.tabela_hist.setItem(row, 1, QTableWidgetItem(nome_cliente))
                self.tabela_hist.setItem(row, 2, QTableWidgetItem(f"R$ {p.get('total', 0):.2f}"))
                
                # Adiciona o botão de PDF que faltava na lógica da tabela
                btn_pdf = QPushButton("Gerar PDF")
                btn_pdf.clicked.connect(lambda checked, arg=i: self.gerar_pdf_pedido(arg))
                self.tabela_hist.setCellWidget(row, 3, btn_pdf)

    def preparar_edicao(self, index):
        p = self.pedidos[index]
        self.pedido_em_edicao_index = index
        self.input_cliente.setText(p["cliente"]["nome"])
        self.itens_pedido_atual = list(p["itens"])
        self.atualizar_tabela_novo()
        self.btn_salvar.setText("✅ ATUALIZAR PEDIDO")
        self.abas.setCurrentWidget(self.aba_novo)

    def excluir_pedido(self, index):
        if QMessageBox.question(self, "Confirmar", "Excluir permanentemente?") == QMessageBox.Yes:
            self.pedidos.pop(index)
            salvar_json(self.pedidos, ARQUIVO_PEDIDOS)
            self.atualizar_hist()

    def gerar_pdf_pedido(self, pedido):
        caminho, _ = QFileDialog.getSaveFileName(self, "Salvar Proposta", f"Proposta_{pedido['numero']}.pdf", "PDF Files (*.pdf)")
        if not caminho: return

        doc = SimpleDocTemplate(caminho, pagesize=A4, rightMargin=45, leftMargin=45, topMargin=45, bottomMargin=45)
        styles = getSampleStyleSheet()
        elementos = []
        largura_a4, altura_a4 = A4 

        def desenhar_moldura(canvas, doc):
            canvas.saveState()
            canvas.setStrokeColor(colors.darkgreen); canvas.setLineWidth(1.5)
            canvas.rect(25, 25, largura_a4 - 50, altura_a4 - 50)
            canvas.setFont('Helvetica-Oblique', 8)
            canvas.drawString(40, 35, f"Iorli Representações - Proposta #{pedido['numero']}")
            canvas.drawRightString(largura_a4 - 40, 35, f"Página {doc.page}")
            canvas.restoreState()

        logo_path = os.path.join(os.path.abspath("."), "logoverde.png")
        img = Image(logo_path, width=80, height=80) if os.path.exists(logo_path) else Spacer(1, 80)
        
        dados_emp = [
            ["Iorli de Fatima Marcondes Rosa Representações"],
            ["CNPJ: 34.308.499/0001-10 | IE: 1706084.2144-6"],
            ["R. Arcendino Rosa Neves 278 - Xaxim, Curitiba - PR"],
            ["Telefone: (41) 99914-7644 | Email: nelsonrosaperfis@yahoo.com.br"]
        ]
        t_emp = Table(dados_emp, colWidths=[400]); t_emp.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'RIGHT'), ('FONTSIZE', (0,0), (-1,-1), 9)]))
        elementos.append(Table([[img, t_emp]], colWidths=[100, 400]))
        elementos.append(Spacer(1, 10))
        elementos.append(Table([[""]], colWidths=[500], rowHeights=[2], style=[('BACKGROUND', (0,0), (-1,-1), colors.darkgreen)]))
        elementos.append(Spacer(1, 15))

        elementos.append(Paragraph(f"<b>PROPOSTA COMERCIAL Nº {pedido['numero']}</b>", styles['Title']))
        elementos.append(Paragraph(f"Data: {pedido['data']}", styles['Normal']))
        elementos.append(Spacer(1, 15))

        cli = pedido["cliente"]
        d_cli = [
            [Paragraph("<b>DADOS DO CLIENTE</b>", styles['Normal']), ""],
            [f"Nome: {cli.get('nome','')}", f"CPF/CNPJ: {cli.get('cpf_cnpj','')}"],
            [f"Cidade: {cli.get('cidade','')} - {cli.get('estado','')}", f"Telefone: {cli.get('telefone','')}"]
        ]
        t_c = Table(d_cli, colWidths=[250, 250]); t_c.setStyle(TableStyle([('SPAN', (0,0), (1,0)), ('BACKGROUND', (0,0), (1,0), colors.whitesmoke), ('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
        elementos.append(t_c); elementos.append(Spacer(1, 20))

        # Itens com CÓDIGO no PDF
        itens_pdf = [["Cód", "Descrição do Perfil", "Qtd", "Peso Tot.", "Subtotal"]]
        for i in pedido["itens"]:
            itens_pdf.append([str(i.get("codigo", "")), i["nome"], str(i["qtd"]), f"{i['peso_total']:.2f}kg", f"R$ {i['subtotal']:.2f}"])
        itens_pdf.append(["", "", "", "TOTAL:", f"R$ {pedido['total']:.2f}"])
        
        t_i = Table(itens_pdf, colWidths=[50, 210, 60, 90, 90])
        estilo = [('BACKGROUND', (0,0), (-1,0), colors.darkgreen), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), ('GRID', (0,0), (-1,-2), 0.5, colors.grey), ('FONTSIZE', (0,-1), (-1,-1), 12)]
        for r in range(1, len(itens_pdf)-1):
            if r % 2 == 0: estilo.append(('BACKGROUND', (0,r), (-1,r), colors.whitesmoke))
        t_i.setStyle(TableStyle(estilo))
        elementos.append(t_i)

        doc.build(elementos, onFirstPage=desenhar_moldura, onLaterPages=desenhar_moldura)
        QMessageBox.information(self, "Sucesso", "PDF Gerado!")
