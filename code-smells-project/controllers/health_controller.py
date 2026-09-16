from flask import jsonify

from config import settings
from constants import VERSION
from models import pedido_model, produto_model, usuario_model


def check():
    counts = {
        "produtos": produto_model.contar(),
        "usuarios": usuario_model.contar(),
        "pedidos": pedido_model.contar(),
    }
    return jsonify({
        "status": "ok",
        "database": "connected",
        "counts": counts,
        "versao": VERSION,
        "ambiente": settings.APP_ENV,
    }), 200
