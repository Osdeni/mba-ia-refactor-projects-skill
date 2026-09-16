"""Guarda de rotas administrativas via header `X-Admin-Token` (valor de ADMIN_TOKEN)."""
import hmac
from functools import wraps

from flask import request

from config import settings
from errors import ForbiddenError, UnauthorizedError

ADMIN_HEADER = "X-Admin-Token"


def require_admin(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not settings.ADMIN_TOKEN:
            raise ForbiddenError("Rotas administrativas desabilitadas (ADMIN_TOKEN não configurado)")
        token = request.headers.get(ADMIN_HEADER, "")
        if not hmac.compare_digest(token, settings.ADMIN_TOKEN):
            raise UnauthorizedError("Token administrativo inválido")
        return view(*args, **kwargs)

    return wrapper
