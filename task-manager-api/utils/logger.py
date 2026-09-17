"""Logger padrão da aplicação (substitui os `print` espalhados pelas rotas)."""
import logging

_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def configure_logging(level="INFO"):
    logging.basicConfig(level=getattr(logging, str(level).upper(), logging.INFO), format=_FORMAT)


def get_logger(name):
    return logging.getLogger(name)
