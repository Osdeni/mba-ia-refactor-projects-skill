from flask import jsonify, request

from models import pedido_model
from services import pedido_service
from validators import pedido_validator


def criar():
    payload = pedido_validator.validar_criacao(request.get_json(silent=True))
    resultado = pedido_service.criar_pedido(payload["usuario_id"], payload["itens"])
    return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201


def listar():
    pedidos = pedido_model.listar()
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def listar_por_usuario(usuario_id):
    pedidos = pedido_model.listar(usuario_id=usuario_id)
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def atualizar_status(pedido_id):
    novo_status = pedido_validator.validar_status(request.get_json(silent=True))
    pedido_service.atualizar_status(pedido_id, novo_status)
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
