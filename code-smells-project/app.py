"""Entry point / composition root. Execução: `python app.py` (configuração via variáveis de ambiente)."""
from flask import Flask
from flask_cors import CORS

from config import settings
from database import connection
from middlewares.error_handler import register_error_handlers
from routes import register_blueprints
from utils.logger import get_logger

log = get_logger(__name__)


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(settings)
    if config:
        app.config.update(config)

    if app.config["SECRET_KEY"] == settings.SECRET_KEY_DEFAULT:
        log.warning("SECRET_KEY padrão em uso — defina SECRET_KEY no ambiente")

    CORS(app, origins=settings.CORS_ORIGINS)
    connection.init_app(app)
    register_blueprints(app)
    register_error_handlers(app)
    return app


app = create_app()

if __name__ == "__main__":
    log.info("Servidor iniciado em http://%s:%s (debug=%s)", settings.HOST, settings.PORT, settings.DEBUG)
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
