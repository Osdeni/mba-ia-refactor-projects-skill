"""Tratamento centralizado de erros: envelope `{"error": <mensagem>}` em todas as respostas de erro."""
from flask import jsonify
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException

from database import db
from errors import AppError
from utils.logger import get_logger

logger = get_logger(__name__)

ERROR_ENVELOPE = "error"
INTERNAL_ERROR_MESSAGE = "Erro interno"
INTEGRITY_ERROR_MESSAGE = "Violação de integridade dos dados"


def _error_response(message, status):
    return jsonify({ERROR_ENVELOPE: message}), status


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(error):
        db.session.rollback()
        return _error_response(error.message, error.status)

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(error):
        db.session.rollback()
        logger.warning("Violação de integridade: %s", error.orig)
        return _error_response(INTEGRITY_ERROR_MESSAGE, 409)

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        return _error_response(error.description, error.code)

    @app.errorhandler(Exception)
    def handle_unexpected(error):
        db.session.rollback()
        logger.exception("Erro não tratado")
        return _error_response(INTERNAL_ERROR_MESSAGE, 500)
