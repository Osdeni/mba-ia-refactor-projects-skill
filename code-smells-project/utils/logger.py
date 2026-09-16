"""Logger da aplicação (substitui os `print` espalhados). Nunca registrar senhas, segredos ou PII."""
import logging

from config import settings

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


def get_logger(name):
    return logging.getLogger(name)
