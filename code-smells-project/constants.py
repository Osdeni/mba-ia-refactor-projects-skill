"""Constantes de domínio (regras de negócio explícitas, sem números mágicos espalhados)."""

VERSION = "1.0.0"

# Produtos
CATEGORIAS_VALIDAS = ("informatica", "moveis", "vestuario", "geral", "eletronicos", "livros")
CATEGORIA_PADRAO = "geral"
NOME_PRODUTO_MIN = 2
NOME_PRODUTO_MAX = 200

# Usuários
TIPO_USUARIO_PADRAO = "cliente"
SENHA_MIN = 6

# Pedidos
STATUS_PEDIDO = ("pendente", "aprovado", "enviado", "entregue", "cancelado")
STATUS_PEDIDO_INICIAL = "pendente"

# Relatório de vendas: (faturamento acima de, taxa de desconto) — avaliadas em ordem
FAIXAS_DESCONTO = ((10000, 0.10), (5000, 0.05), (1000, 0.02))
