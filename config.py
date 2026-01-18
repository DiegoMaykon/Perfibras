import os
from pathlib import Path

def criar_pasta_dados():
    r"""
    Cria a pasta de dados dentro do diretório do usuário (AppData\\Roaming\\NelsonRosa\\dados).
    Essa abordagem é ideal para programas instalados com Inno Setup.
    """
    pasta_base = Path(os.getenv("APPDATA"))  # Exemplo: C:\Users\Diego\AppData\Roaming
    pasta_dados = pasta_base / "NelsonRosa" / "dados"
    pasta_dados.mkdir(parents=True, exist_ok=True)
    return pasta_dados


# ✅ Caminho base de dados
PASTA_DADOS = criar_pasta_dados()

# ✅ Caminhos completos dos arquivos JSON
ARQUIVO_CLIENTES = PASTA_DADOS / "clientes.json"
ARQUIVO_ACESSORIOS = PASTA_DADOS / "acessorios.json"
ARQUIVO_PEDIDOS = PASTA_DADOS / "pedidos.json"

# ✅ Lista principal usada para backup ou referência
ARQUIVOS_SISTEMA = [ARQUIVO_CLIENTES, ARQUIVO_ACESSORIOS, ARQUIVO_PEDIDOS]

print("📂 Pasta de dados:", PASTA_DADOS)