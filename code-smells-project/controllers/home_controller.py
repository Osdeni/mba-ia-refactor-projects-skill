from flask import jsonify

from constants import VERSION


def index():
    return jsonify({
        "mensagem": "Bem-vindo à API da Loja",
        "versao": VERSION,
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        },
    }), 200
