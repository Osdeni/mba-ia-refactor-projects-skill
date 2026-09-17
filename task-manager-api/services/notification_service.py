"""Gateway de notificação por e-mail, configurado por ambiente (SMTP_*).

Sem `SMTP_HOST` configurado, as notificações são apenas registradas no log — a app nunca
tenta abrir conexão de rede por padrão e nenhuma credencial vive no código.
"""
import smtplib
from email.message import EmailMessage

from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)


def is_configured():
    return bool(settings.SMTP_HOST)


def send_email(to, subject, body):
    """True quando o e-mail foi entregue ao servidor SMTP; False caso contrário (nunca levanta)."""
    if not is_configured():
        logger.info("SMTP não configurado — notificação para %s ignorada (%s)", to, subject)
        return False

    message = EmailMessage()
    message["From"] = settings.SMTP_FROM
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(message)
        logger.info("Email enviado para %s", to)
        return True
    except (smtplib.SMTPException, OSError) as error:
        logger.error("Erro ao enviar email para %s: %s", to, error.__class__.__name__)
        return False


def notify_task_assigned(user, task):
    subject = f"Nova task atribuída: {task.title}"
    body = (
        f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\n"
        f"Prioridade: {task.priority}\nStatus: {task.status}"
    )
    return send_email(user.email, subject, body)


def notify_task_overdue(user, task):
    subject = f"Task atrasada: {task.title}"
    body = f"Olá {user.name},\n\nA task '{task.title}' está atrasada!\n\nData limite: {task.due_date}"
    return send_email(user.email, subject, body)
