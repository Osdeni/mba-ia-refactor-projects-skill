"""Hash de senhas com KDF (werkzeug, já disponível via Flask) e verificação legada.

Bancos criados antes da refatoração guardam senhas em texto puro; `verify_password` aceita esse
formato e sinaliza `needs_upgrade` para que o login regrave a senha com hash.
"""
import hmac

from werkzeug.security import check_password_hash, generate_password_hash

MODERN_PREFIXES = ("scrypt:", "pbkdf2:")


def hash_password(raw):
    return generate_password_hash(raw)


def verify_password(stored, raw):
    """Retorna (ok, needs_upgrade)."""
    if not stored or raw is None:
        return False, False
    if stored.startswith(MODERN_PREFIXES):
        return check_password_hash(stored, raw), False
    return hmac.compare_digest(stored, raw), True  # legado em texto puro
