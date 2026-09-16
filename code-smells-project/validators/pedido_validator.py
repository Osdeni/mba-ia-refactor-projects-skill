"""Validação de entrada de pedidos (mensagens originais preservadas)."""
from constants import STATUS_PEDIDO
from errors import ValidationError


def _inteiro_positivo(valor):
    return isinstance(valor, int) and not isinstance(valor, bool) and valor > 0


def _validar_item(item):
    if not isinstance(item, dict) or "produto_id" not in item or "quantidade" not in item:
        raise ValidationError("Item inválido: produto_id e quantidade são obrigatórios")
    if not _inteiro_positivo(item["produto_id"]):
        raise ValidationError("produto_id inválido")
    if not _inteiro_positivo(item["quantidade"]):
        raise ValidationError("Quantidade deve ser um inteiro positivo")
    return {"produto_id": item["produto_id"], "quantidade": item["quantidade"]}


def validar_criacao(dados):
    if not dados or not isinstance(dados, dict):
        raise ValidationError("Dados inválidos")
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])
    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    if not _inteiro_positivo(usuario_id):
        raise ValidationError("Usuario ID inválido")
    if not isinstance(itens, list) or len(itens) == 0:
        raise ValidationError("Pedido deve ter pelo menos 1 item")
    return {"usuario_id": usuario_id, "itens": [_validar_item(item) for item in itens]}


def validar_status(dados):
    if not isinstance(dados, dict):
        dados = {}
    status = dados.get("status", "")
    if status not in STATUS_PEDIDO:
        raise ValidationError("Status inválido")
    return status
