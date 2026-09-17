"""Criação/atualização de tasks: checa as referências (usuário, categoria) e notifica atribuição."""
from errors import NotFoundError
from models.category import Category
from models.task import Task
from models.user import User
from services import notification_service
from utils.logger import get_logger

logger = get_logger(__name__)

MSG_USER_NOT_FOUND = "Usuário não encontrado"
MSG_CATEGORY_NOT_FOUND = "Categoria não encontrada"


def _ensure_references(payload):
    """404 quando user_id/category_id apontam para registros inexistentes (mesma ordem original)."""
    if payload.get("user_id"):
        if not User.get(payload["user_id"]):
            raise NotFoundError(MSG_USER_NOT_FOUND)
    if payload.get("category_id"):
        if not Category.get(payload["category_id"]):
            raise NotFoundError(MSG_CATEGORY_NOT_FOUND)


def create_task(payload):
    _ensure_references(payload)
    task = Task.create(payload)
    logger.info("Task criada: %s - %s", task.id, task.title)
    if task.user:
        notification_service.notify_task_assigned(task.user, task)
    return task


def update_task(task, changes):
    _ensure_references(changes)
    previous_user_id = task.user_id
    task.update(changes)
    logger.info("Task atualizada: %s", task.id)
    if task.user and task.user_id != previous_user_id:
        notification_service.notify_task_assigned(task.user, task)
    return task


def delete_task(task):
    task_id = task.id
    task.delete()
    logger.info("Task deletada: %s", task_id)
