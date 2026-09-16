from flask import Blueprint

from controllers import pedido_controller as c

bp = Blueprint("pedidos", __name__)

bp.add_url_rule("/pedidos", "criar", c.criar, methods=["POST"])
bp.add_url_rule("/pedidos", "listar", c.listar, methods=["GET"])
bp.add_url_rule("/pedidos/usuario/<int:usuario_id>", "listar_por_usuario", c.listar_por_usuario, methods=["GET"])
bp.add_url_rule("/pedidos/<int:pedido_id>/status", "atualizar_status", c.atualizar_status, methods=["PUT"])
