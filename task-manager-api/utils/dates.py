"""Helpers de data: UTC naive (compatível com o schema e com `str(created_at)` da API)."""
from datetime import datetime, timezone

from utils.constants import DATE_FORMAT


def utcnow():
    """Agora em UTC, sem tzinfo — substitui o deprecado `datetime.utcnow()`."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def parse_date(value):
    """`YYYY-MM-DD` → datetime; None quando o valor não está nesse formato."""
    if not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value, DATE_FORMAT)
    except ValueError:
        return None


def format_date(value):
    return str(value) if value else None
