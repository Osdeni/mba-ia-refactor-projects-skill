from flask import jsonify, request

from errors import UnauthorizedError
from services import auth_service
from validators import usuario_validator


def login():
    credenciais = usuario_validator.validar_login(request.get_json(silent=True))
    usuario = auth_service.login(credenciais["email"], credenciais["senha"])
    if usuario is None:
        raise UnauthorizedError("Email ou senha inválidos")
    return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
