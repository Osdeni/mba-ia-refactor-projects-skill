from flask import Blueprint

from controllers import auth_controller, usuario_controller as c

bp = Blueprint("usuarios", __name__)

bp.add_url_rule("/usuarios", "listar", c.listar, methods=["GET"])
bp.add_url_rule("/usuarios/<int:usuario_id>", "buscar", c.buscar, methods=["GET"])
bp.add_url_rule("/usuarios", "criar", c.criar, methods=["POST"])
bp.add_url_rule("/login", "login", auth_controller.login, methods=["POST"])
