"""Validação de entrada de usuários e login (mensagens originais preservadas)."""
import re

from constants import SENHA_MIN
from errors import ValidationError

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _texto(dados, campo):
    valor = dados.get(campo, "")
    return valor.strip() if isinstance(valor, str) else ""


def validar_criacao(dados):
    if not dados or not isinstance(dados, dict):
        raise ValidationError("Dados inválidos")
    nome, email, senha = _texto(dados, "nome"), _texto(dados, "email"), dados.get("senha", "")
    if not nome or not email or not senha:
        raise ValidationError("Nome, email e senha são obrigatórios")
    if not _EMAIL_RE.match(email):
        raise ValidationError("Email inválido")
    if not isinstance(senha, str) or len(senha) < SENHA_MIN:
        raise ValidationError(f"Senha deve ter pelo menos {SENHA_MIN} caracteres")
    return {"nome": nome, "email": email.lower(), "senha": senha}


def validar_login(dados):
    if not isinstance(dados, dict):
        dados = {}
    email, senha = _texto(dados, "email"), dados.get("senha", "")
    if not email or not senha or not isinstance(senha, str):
        raise ValidationError("Email e senha são obrigatórios")
    return {"email": email.lower(), "senha": senha}
