"""Configuração lida do ambiente com defaults seguros.

A aplicação precisa subir sem `.env` e sem variáveis exportadas; por isso todo valor tem
default. Segredos usam valores claramente de desenvolvimento e geram aviso no log.
"""
import logging
import os

from dotenv import load_dotenv

load_dotenv()

_DEV_SECRET = "dev-only-change-me"


def _bool(name, default):
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes")


def _int(name, default):
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _optional(name):
    value = os.getenv(name, "").strip()
    return value or None


# --- Flask ---------------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", _DEV_SECRET)
DEBUG = _bool("DEBUG", False)
HOST = os.getenv("HOST", "127.0.0.1")
PORT = _int("PORT", 5000)
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# --- Banco de dados --------------------------------------------------------
# Mesmo caminho da versão original (Flask-SQLAlchemy resolve para instance/tasks.db).
SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///tasks.db")

# --- Autenticação ----------------------------------------------------------
ADMIN_TOKEN = _optional("ADMIN_TOKEN")          # None → rotas administrativas respondem 403
TOKEN_MAX_AGE = _int("TOKEN_MAX_AGE", 86400)    # validade do token de login, em segundos

# --- Notificações por e-mail (opcional; sem SMTP_HOST as notificações só são logadas) ---
SMTP_HOST = _optional("SMTP_HOST")
SMTP_PORT = _int("SMTP_PORT", 587)
SMTP_USER = _optional("SMTP_USER")
SMTP_PASSWORD = _optional("SMTP_PASSWORD")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER or "taskmanager@localhost")

if SECRET_KEY == _DEV_SECRET:
    logging.getLogger(__name__).warning(
        "SECRET_KEY padrão de desenvolvimento em uso — defina SECRET_KEY no ambiente"
    )
