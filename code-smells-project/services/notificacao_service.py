"""Notificações de pedido (e-mail/SMS/push). Hoje apenas registra em log; ponto único para
plugar um gateway real sem tocar em controllers."""
from utils.logger import get_logger

log = get_logger(__name__)


def pedido_criado(pedido_id, usuario_id):
    log.info("EMAIL: pedido %s criado para usuário %s", pedido_id, usuario_id)
    log.info("SMS: pedido %s recebido", pedido_id)
    log.info("PUSH: novo pedido %s recebido pelo sistema", pedido_id)


def pedido_aprovado(pedido_id):
    log.info("NOTIFICAÇÃO: pedido %s aprovado — preparar envio", pedido_id)


def pedido_cancelado(pedido_id):
    log.info("NOTIFICAÇÃO: pedido %s cancelado — devolver estoque", pedido_id)
