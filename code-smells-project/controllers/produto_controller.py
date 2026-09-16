from flask import jsonify, request

from errors import NotFoundError
from models import produto_model
from validators import produto_validator

PRODUTO_NAO_ENCONTRADO = "Produto não encontrado"


def listar():
    produtos = produto_model.listar()
    return jsonify({"dados": produtos, "sucesso": True}), 200


def buscar(produto_id):
    produto = produto_model.buscar_por_id(produto_id)
    if produto is None:
        raise NotFoundError(PRODUTO_NAO_ENCONTRADO)
    return jsonify({"dados": produto, "sucesso": True}), 200


def pesquisar():
    filtros = produto_validator.validar_busca(request.args)
    resultados = produto_model.buscar(**filtros)
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200


def criar():
    payload = produto_validator.validar(request.get_json(silent=True))
    produto_id = produto_model.criar(payload)
    return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201


def atualizar(produto_id):
    if produto_model.buscar_por_id(produto_id) is None:
        raise NotFoundError(PRODUTO_NAO_ENCONTRADO)
    payload = produto_validator.validar(request.get_json(silent=True))
    produto_model.atualizar(produto_id, payload)
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


def deletar(produto_id):
    if not produto_model.deletar(produto_id):
        raise NotFoundError(PRODUTO_NAO_ENCONTRADO)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
