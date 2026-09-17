"""Validação de categorias (create / update)."""
from errors import ValidationError
from utils.constants import COLOR_REGEX, DEFAULT_COLOR

MSG_INVALID_DATA = "Dados inválidos"
MSG_NAME_REQUIRED = "Nome é obrigatório"
MSG_COLOR_INVALID = "Cor inválida. Use #RRGGBB"


def _require_body(data):
    if not isinstance(data, dict) or not data:
        raise ValidationError(MSG_INVALID_DATA)


def _clean_name(value):
    name = str(value).strip() if value is not None else ""
    if not name:
        raise ValidationError(MSG_NAME_REQUIRED)
    return name


def _clean_color(value):
    if not isinstance(value, str) or not COLOR_REGEX.match(value):
        raise ValidationError(MSG_COLOR_INVALID)
    return value


def validate_create(data):
    _require_body(data)
    if not data.get("name"):
        raise ValidationError(MSG_NAME_REQUIRED)
    return {
        "name": _clean_name(data["name"]),
        "description": data.get("description", ""),
        "color": _clean_color(data.get("color", DEFAULT_COLOR)),
    }


def validate_update(data):
    _require_body(data)
    changes = {}
    if "name" in data:
        changes["name"] = _clean_name(data["name"])
    if "description" in data:
        changes["description"] = data["description"]
    if "color" in data:
        changes["color"] = _clean_color(data["color"])
    return changes
