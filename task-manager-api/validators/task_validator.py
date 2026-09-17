"""Validação de tasks (create / update / search) — fonte única das regras de campo."""
from errors import ValidationError
from utils.constants import (
    DEFAULT_PRIORITY,
    DEFAULT_STATUS,
    MAX_PRIORITY,
    MAX_TITLE_LENGTH,
    MIN_PRIORITY,
    MIN_TITLE_LENGTH,
    TAGS_SEPARATOR,
    VALID_STATUSES,
)
from utils.dates import parse_date

MSG_INVALID_DATA = "Dados inválidos"
MSG_TITLE_REQUIRED = "Título é obrigatório"
MSG_TITLE_INVALID = "Título inválido"
MSG_TITLE_SHORT = "Título muito curto"
MSG_TITLE_LONG = "Título muito longo"
MSG_STATUS_INVALID = "Status inválido"
MSG_PRIORITY_RANGE = f"Prioridade deve ser entre {MIN_PRIORITY} e {MAX_PRIORITY}"
MSG_PRIORITY_INVALID = "Prioridade inválida"
MSG_USER_ID_INVALID = "Usuário inválido"
MSG_CATEGORY_ID_INVALID = "Categoria inválida"
MSG_DATE_INVALID_CREATE = "Formato de data inválido. Use YYYY-MM-DD"
MSG_DATE_INVALID_UPDATE = "Formato de data inválido"
MSG_TAGS_INVALID = "Tags inválidas"


def _require_body(data):
    if not isinstance(data, dict) or not data:
        raise ValidationError(MSG_INVALID_DATA)


def _to_int(value):
    """int estrito: aceita int e strings numéricas; rejeita bool, floats e lixo."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().lstrip("-").isdigit():
        return int(value.strip())
    return None


def _clean_title(value):
    if not isinstance(value, str):
        raise ValidationError(MSG_TITLE_INVALID)
    if len(value) < MIN_TITLE_LENGTH:
        raise ValidationError(MSG_TITLE_SHORT)
    if len(value) > MAX_TITLE_LENGTH:
        raise ValidationError(MSG_TITLE_LONG)
    return value


def _clean_status(value):
    if value not in VALID_STATUSES:
        raise ValidationError(MSG_STATUS_INVALID)
    return value


def _clean_priority(value):
    priority = _to_int(value)
    if priority is None or priority < MIN_PRIORITY or priority > MAX_PRIORITY:
        raise ValidationError(MSG_PRIORITY_RANGE)
    return priority


def _clean_optional_id(value, message):
    """Chaves estrangeiras: None/0/"" viram None (mesma semântica do `if user_id:` original)."""
    if not value:
        return None
    ident = _to_int(value)
    if ident is None or ident < 1:
        raise ValidationError(message)
    return ident


def _clean_due_date(value, message):
    if not value:
        return None
    parsed = parse_date(value)
    if parsed is None:
        raise ValidationError(message)
    return parsed


def _clean_tags(value):
    if value is None or value == "" or value == []:
        return None
    if isinstance(value, list):
        return TAGS_SEPARATOR.join(str(tag) for tag in value)
    if isinstance(value, str):
        return value
    raise ValidationError(MSG_TAGS_INVALID)


def validate_create(data):
    _require_body(data)
    title = data.get("title")
    if not title:
        raise ValidationError(MSG_TITLE_REQUIRED)

    payload = {
        "title": _clean_title(title),
        "description": data.get("description", ""),
        "status": _clean_status(data.get("status", DEFAULT_STATUS)),
        "priority": _clean_priority(data.get("priority", DEFAULT_PRIORITY)),
        "user_id": _clean_optional_id(data.get("user_id"), MSG_USER_ID_INVALID),
        "category_id": _clean_optional_id(data.get("category_id"), MSG_CATEGORY_ID_INVALID),
        "due_date": _clean_due_date(data.get("due_date"), MSG_DATE_INVALID_CREATE),
        "tags": _clean_tags(data.get("tags")),
    }
    return payload


def validate_update(data):
    _require_body(data)
    changes = {}
    if "title" in data:
        changes["title"] = _clean_title(data["title"])
    if "description" in data:
        changes["description"] = data["description"]
    if "status" in data:
        changes["status"] = _clean_status(data["status"])
    if "priority" in data:
        changes["priority"] = _clean_priority(data["priority"])
    if "user_id" in data:
        changes["user_id"] = _clean_optional_id(data["user_id"], MSG_USER_ID_INVALID)
    if "category_id" in data:
        changes["category_id"] = _clean_optional_id(data["category_id"], MSG_CATEGORY_ID_INVALID)
    if "due_date" in data:
        changes["due_date"] = _clean_due_date(data["due_date"], MSG_DATE_INVALID_UPDATE)
    if "tags" in data:
        changes["tags"] = _clean_tags(data["tags"])
    return changes


def validate_search(args):
    """Query string de GET /tasks/search: filtros vazios são ignorados, inválidos viram 400."""
    filters = {"query": args.get("q", "") or None, "status": args.get("status", "") or None}

    priority = args.get("priority", "")
    if priority:
        filters["priority"] = _to_int(priority)
        if filters["priority"] is None:
            raise ValidationError(MSG_PRIORITY_INVALID)

    user_id = args.get("user_id", "")
    if user_id:
        filters["user_id"] = _to_int(user_id)
        if filters["user_id"] is None:
            raise ValidationError(MSG_USER_ID_INVALID)

    return filters
