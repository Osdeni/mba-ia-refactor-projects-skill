"""Guarda administrativa baseada em token de ambiente (header X-Admin-Token)."""
import hmac
from functools import wraps

from flask import request

from config import settings
from errors import ForbiddenError, UnauthorizedError

ADMIN_HEADER = "X-Admin-Token"
ADMIN_DISABLED_MESSAGE = "Operação administrativa desabilitada (ADMIN_TOKEN não configurado)"
ADMIN_INVALID_MESSAGE = "Token administrativo inválido"


def check_admin():
    """Levanta 403 se ADMIN_TOKEN não está configurado e 401 se o header não confere."""
    if not settings.ADMIN_TOKEN:
        raise ForbiddenError(ADMIN_DISABLED_MESSAGE)
    provided = request.headers.get(ADMIN_HEADER, "")
    if not hmac.compare_digest(provided, settings.ADMIN_TOKEN):
        raise UnauthorizedError(ADMIN_INVALID_MESSAGE)


def require_admin(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        check_admin()
        return view(*args, **kwargs)

    return wrapper
