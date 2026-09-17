"""Validação de usuários (create / update / login) — fonte única das regras de campo."""
from errors import ValidationError
from utils.constants import DEFAULT_ROLE, EMAIL_REGEX, MIN_PASSWORD_LENGTH, VALID_ROLES

MSG_INVALID_DATA = "Dados inválidos"
MSG_NAME_REQUIRED = "Nome é obrigatório"
MSG_EMAIL_REQUIRED = "Email é obrigatório"
MSG_PASSWORD_REQUIRED = "Senha é obrigatória"
MSG_EMAIL_INVALID = "Email inválido"
MSG_PASSWORD_MIN = f"Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres"
MSG_PASSWORD_SHORT = "Senha muito curta"
MSG_ROLE_INVALID = "Role inválido"
MSG_ACTIVE_INVALID = "Campo active deve ser booleano"
MSG_CREDENTIALS_REQUIRED = "Email e senha são obrigatórios"


def _require_body(data):
    if not isinstance(data, dict) or not data:
        raise ValidationError(MSG_INVALID_DATA)


def _clean_name(value):
    name = str(value).strip() if value is not None else ""
    if not name:
        raise ValidationError(MSG_NAME_REQUIRED)
    return name


def _clean_email(value):
    if not isinstance(value, str) or not EMAIL_REGEX.match(value.strip()):
        raise ValidationError(MSG_EMAIL_INVALID)
    return value.strip()


def _clean_password(value, short_message):
    if not isinstance(value, str) or len(value) < MIN_PASSWORD_LENGTH:
        raise ValidationError(short_message)
    return value


def _clean_role(value):
    if value not in VALID_ROLES:
        raise ValidationError(MSG_ROLE_INVALID)
    return value


def validate_create(data):
    _require_body(data)
    name, email, password = data.get("name"), data.get("email"), data.get("password")
    role = data.get("role", DEFAULT_ROLE)

    if not name:
        raise ValidationError(MSG_NAME_REQUIRED)
    if not email:
        raise ValidationError(MSG_EMAIL_REQUIRED)
    if not password:
        raise ValidationError(MSG_PASSWORD_REQUIRED)

    return {
        "name": _clean_name(name),
        "email": _clean_email(email),
        "password": _clean_password(password, MSG_PASSWORD_MIN),
        "role": _clean_role(role),
    }


def validate_update(data):
    _require_body(data)
    changes = {}
    if "name" in data:
        changes["name"] = _clean_name(data["name"])
    if "email" in data:
        changes["email"] = _clean_email(data["email"])
    if "password" in data:
        changes["password"] = _clean_password(data["password"], MSG_PASSWORD_SHORT)
    if "role" in data:
        changes["role"] = _clean_role(data["role"])
    if "active" in data:
        if not isinstance(data["active"], bool):
            raise ValidationError(MSG_ACTIVE_INVALID)
        changes["active"] = data["active"]
    return changes


def validate_login(data):
    _require_body(data)
    email, password = data.get("email"), data.get("password")
    if not email or not password:
        raise ValidationError(MSG_CREDENTIALS_REQUIRED)
    if not isinstance(email, str) or not isinstance(password, str):
        raise ValidationError(MSG_CREDENTIALS_REQUIRED)
    return {"email": email, "password": password}
