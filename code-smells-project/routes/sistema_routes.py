"""Rotas de sistema: raiz, health check e administração."""
from flask import Blueprint

from controllers import admin_controller, health_controller, home_controller

bp = Blueprint("sistema", __name__)

bp.add_url_rule("/", "index", home_controller.index, methods=["GET"])
bp.add_url_rule("/health", "health", health_controller.check, methods=["GET"])
bp.add_url_rule("/admin/reset-db", "admin_reset_db", admin_controller.reset_db, methods=["POST"])
bp.add_url_rule("/admin/query", "admin_query", admin_controller.query, methods=["POST"])
