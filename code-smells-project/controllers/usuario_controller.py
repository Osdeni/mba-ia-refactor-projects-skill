from flask import jsonify, request

from errors import NotFoundError
from models import usuario_model
from services import usuario_service
from validators import usuario_validator


def listar():
    usuarios = usuario_model.listar()
    return jsonify({"dados": usuarios, "sucesso": True}), 200


def buscar(usuario_id):
    usuario = usuario_model.buscar_por_id(usuario_id)
    if usuario is None:
        raise NotFoundError("Usuário não encontrado")
    return jsonify({"dados": usuario, "sucesso": True}), 200


def criar():
    payload = usuario_validator.validar_criacao(request.get_json(silent=True))
    usuario_id = usuario_service.criar_usuario(payload["nome"], payload["email"], payload["senha"])
    return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201
