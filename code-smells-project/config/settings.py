"""Configurações lidas do ambiente.

Todo valor tem default para que a aplicação suba sem `.env` e sem variáveis exportadas.
Este módulo não importa nada da aplicação.
"""
import os


def _bool(name, default):
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


def _list(name, default):
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


SECRET_KEY_DEFAULT = "dev-only-change-me"

SECRET_KEY = os.getenv("SECRET_KEY", SECRET_KEY_DEFAULT)
DEBUG = _bool("DEBUG", False)
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "5000"))
DB_PATH = os.getenv("DB_PATH", "loja.db")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN") or None  # None → rotas /admin/* respondem 403
CORS_ORIGINS = _list("CORS_ORIGINS", "*")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
APP_ENV = os.getenv("APP_ENV", "development")
