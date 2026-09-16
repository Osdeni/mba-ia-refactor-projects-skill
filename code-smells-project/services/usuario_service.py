"""Cadastro de usuários: unicidade de e-mail e hash da senha."""
from constants import TIPO_USUARIO_PADRAO
from errors import ValidationError
from models import usuario_model
from utils.logger import get_logger
from utils.security import hash_password

log = get_logger(__name__)


def criar_usuario(nome, email, senha):
    if usuario_model.email_existe(email):
        raise ValidationError("Email já cadastrado")
    usuario_id = usuario_model.criar(nome, email, hash_password(senha), TIPO_USUARIO_PADRAO)
    log.info("Usuário criado id=%s", usuario_id)
    return usuario_id
