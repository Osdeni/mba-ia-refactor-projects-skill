"""Autenticação: verifica a senha e migra hashes legados de forma transparente."""
from models import usuario_model
from utils.logger import get_logger
from utils.security import hash_password, verify_password

log = get_logger(__name__)


def login(email, senha):
    """Retorna o usuário público (sem senha) ou None se as credenciais forem inválidas."""
    registro = usuario_model.buscar_credenciais(email)
    if registro is None:
        return None
    ok, precisa_upgrade = verify_password(registro["senha"], senha)
    if not ok:
        log.info("Login falhou para usuário id=%s", registro["id"])
        return None
    if precisa_upgrade:
        usuario_model.atualizar_senha(registro["id"], hash_password(senha))
        log.info("Senha do usuário id=%s migrada para hash", registro["id"])
    log.info("Login bem-sucedido para usuário id=%s", registro["id"])
    return {"id": registro["id"], "nome": registro["nome"], "email": registro["email"], "tipo": registro["tipo"]}
