"""Composition root: cria a app, carrega config, registra banco, blueprints e error handlers.

Continua funcionando `python app.py` e `from app import app, db` (usado pelo seed).
"""
from flask import Flask
from flask_cors import CORS

import database
from config import settings
from database import db  # noqa: F401  — re-exportado para `from app import app, db`
from middlewares.error_handler import register_error_handlers
from routes import register_blueprints
from utils.logger import configure_logging


def _cors_origins(value):
    origins = [origin.strip() for origin in value.split(",") if origin.strip()]
    return "*" if not origins or origins == ["*"] else origins


def create_app(config_object=settings):
    configure_logging(config_object.LOG_LEVEL)
    app = Flask(__name__)
    app.config.from_object(config_object)

    CORS(app, origins=_cors_origins(config_object.CORS_ORIGINS))
    database.init_app(app)
    register_blueprints(app)
    register_error_handlers(app)
    return app


app = create_app()

if __name__ == "__main__":
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
