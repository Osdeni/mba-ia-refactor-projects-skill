"""Handler central de erros: envelope `{"erro": ..., "sucesso": false}` e status corretos.
Nunca devolve `str(e)` de exceções internas ao cliente."""
from flask import jsonify
from werkzeug.exceptions import HTTPException

from errors import AppError
from utils.logger import get_logger

log = get_logger(__name__)

ENVELOPE = "erro"


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(error):
        return jsonify({ENVELOPE: error.message, "sucesso": False}), error.status

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        return jsonify({ENVELOPE: error.description, "sucesso": False}), error.code

    @app.errorhandler(Exception)
    def handle_unexpected(error):
        log.exception("Erro não tratado")
        return jsonify({ENVELOPE: "Erro interno", "sucesso": False}), 500
