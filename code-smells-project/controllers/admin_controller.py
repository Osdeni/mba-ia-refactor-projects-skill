from flask import jsonify, request

from middlewares.auth import require_admin
from services import admin_service


@require_admin
def reset_db():
    admin_service.resetar_banco()
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200


@require_admin
def query():
    dados = request.get_json(silent=True) or {}
    resultado = admin_service.executar_consulta(dados.get("sql", ""))
    return jsonify({"dados": resultado, "sucesso": True}), 200
