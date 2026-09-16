"""Caso de uso de pedidos: criação transacional com baixa de estoque e mudança de status."""
from constants import STATUS_PEDIDO_INICIAL
from database.connection import transaction
from errors import NotFoundError, ValidationError
from models import pedido_model, produto_model, usuario_model
from services import notificacao_service


def criar_pedido(usuario_id, itens):
    with transaction():
        if usuario_model.buscar_por_id(usuario_id) is None:
            raise ValidationError("Usuário não encontrado")

        total = 0
        linhas = []
        for item in itens:
            produto = produto_model.buscar_por_id(item["produto_id"])
            if produto is None:
                raise ValidationError(f"Produto {item['produto_id']} não encontrado")
            if produto["estoque"] < item["quantidade"]:
                raise ValidationError(f"Estoque insuficiente para {produto['nome']}")
            total += produto["preco"] * item["quantidade"]
            linhas.append((item["produto_id"], item["quantidade"], produto["preco"]))

        pedido_id = pedido_model.criar(usuario_id, total, STATUS_PEDIDO_INICIAL)
        pedido_model.adicionar_itens(pedido_id, linhas)
        for produto_id, quantidade, _preco in linhas:
            if not produto_model.baixar_estoque(produto_id, quantidade):
                raise ValidationError(f"Estoque insuficiente para {produto_model.buscar_por_id(produto_id)['nome']}")

    notificacao_service.pedido_criado(pedido_id, usuario_id)
    return {"pedido_id": pedido_id, "total": total}


def atualizar_status(pedido_id, novo_status):
    with transaction():
        if not pedido_model.atualizar_status(pedido_id, novo_status):
            raise NotFoundError("Pedido não encontrado")

    if novo_status == "aprovado":
        notificacao_service.pedido_aprovado(pedido_id)
    elif novo_status == "cancelado":
        notificacao_service.pedido_cancelado(pedido_id)
