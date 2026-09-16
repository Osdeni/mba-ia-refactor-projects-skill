"""Operações administrativas: reset do banco e consulta SQL somente leitura."""
import re
import sqlite3

from database import schema
from database.connection import readonly_connection, transaction
from errors import ValidationError
from utils.logger import get_logger

log = get_logger(__name__)

_SELECT_RE = re.compile(r"^\s*SELECT\b", re.IGNORECASE)


def resetar_banco():
    with transaction() as conn:
        schema.truncate_all(conn)
    log.warning("Banco de dados resetado por requisição administrativa")


def executar_consulta(sql):
    if not isinstance(sql, str) or not sql.strip():
        raise ValidationError("Query não informada")
    if not _SELECT_RE.match(sql):
        raise ValidationError("Apenas consultas SELECT são permitidas")
    with readonly_connection() as conn:
        try:
            rows = conn.execute(sql).fetchall()  # conexão mode=ro; execute() aceita uma única instrução
        except sqlite3.Error as exc:
            raise ValidationError(f"Query inválida: {exc}") from exc
    return [dict(row) for row in rows]
