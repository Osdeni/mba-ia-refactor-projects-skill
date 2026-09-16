from flask import Blueprint

from controllers import produto_controller as c

bp = Blueprint("produtos", __name__)

bp.add_url_rule("/produtos", "listar", c.listar, methods=["GET"])
bp.add_url_rule("/produtos/busca", "pesquisar", c.pesquisar, methods=["GET"])
bp.add_url_rule("/produtos/<int:produto_id>", "buscar", c.buscar, methods=["GET"])
bp.add_url_rule("/produtos", "criar", c.criar, methods=["POST"])
bp.add_url_rule("/produtos/<int:produto_id>", "atualizar", c.atualizar, methods=["PUT"])
bp.add_url_rule("/produtos/<int:produto_id>", "deletar", c.deletar, methods=["DELETE"])
