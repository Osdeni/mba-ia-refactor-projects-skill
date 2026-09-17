"""Login com token assinado (itsdangerous, já dependência do Flask) e upgrade de hashes legados."""
from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from config import settings
from errors import ForbiddenError, UnauthorizedError
from models.user import User
from utils.logger import get_logger

logger = get_logger(__name__)

TOKEN_SALT = "task-manager-auth"
MSG_INVALID_CREDENTIALS = "Credenciais inválidas"
MSG_INACTIVE_USER = "Usuário inativo"


def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt=TOKEN_SALT)


def issue_token(user):
    return _serializer().dumps({"user_id": user.id, "role": user.role})


def verify_token(token):
    """Payload do token ou None quando inválido/expirado."""
    try:
        return _serializer().loads(token, max_age=settings.TOKEN_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None


def login(email, password):
    """Retorna (user, token). Ordem dos erros igual à original: 401, 401, 403."""
    user = User.get_by_email(email)
    if not user:
        raise UnauthorizedError(MSG_INVALID_CREDENTIALS)

    ok, needs_upgrade = user.verify_password(password)
    if not ok:
        raise UnauthorizedError(MSG_INVALID_CREDENTIALS)
    if not user.active:
        raise ForbiddenError(MSG_INACTIVE_USER)

    if needs_upgrade:
        user.update({"password": password})
        logger.info("Hash de senha legado atualizado para o usuário %s", user.id)

    return user, issue_token(user)
