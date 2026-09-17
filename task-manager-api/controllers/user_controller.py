from flask import jsonify, request

from errors import ConflictError, NotFoundError
from middlewares.auth import check_admin
from models.user import User
from services import auth_service
from utils.constants import DEFAULT_ROLE
from utils.logger import get_logger
from validators import user_validator

logger = get_logger(__name__)

MSG_USER_NOT_FOUND = "Usuário não encontrado"
MSG_EMAIL_TAKEN = "Email já cadastrado"
MSG_USER_DELETED = "Usuário deletado com sucesso"
MSG_LOGIN_OK = "Login realizado com sucesso"

# Campos devolvidos por GET /users/<id>/tasks (subconjunto original, com `overdue`)
USER_TASK_FIELDS = ("id", "title", "description", "status", "priority", "created_at", "due_date", "overdue")


def _get_user_or_404(user_id):
    user = User.get(user_id)
    if not user:
        raise NotFoundError(MSG_USER_NOT_FOUND)
    return user


def _ensure_email_available(email, current_user_id=None):
    existing = User.get_by_email(email)
    if existing and existing.id != current_user_id:
        raise ConflictError(MSG_EMAIL_TAKEN)


def list_users():
    result = [{**user.to_dict(), "task_count": task_count} for user, task_count in User.list_with_task_counts()]
    return jsonify(result), 200


def get_user(user_id):
    user = _get_user_or_404(user_id)
    return jsonify(user.to_dict(with_tasks=True)), 200


def create_user():
    payload = user_validator.validate_create(request.get_json(silent=True))
    if payload["role"] != DEFAULT_ROLE:
        check_admin()  # só admins podem cadastrar com role elevado
    _ensure_email_available(payload["email"])
    user = User.create(**payload)
    logger.info("Usuário criado: %s - %s", user.id, user.name)
    return jsonify(user.to_dict()), 201


def update_user(user_id):
    user = _get_user_or_404(user_id)
    changes = user_validator.validate_update(request.get_json(silent=True))
    if "role" in changes or "active" in changes:
        check_admin()
    if "email" in changes:
        _ensure_email_available(changes["email"], current_user_id=user_id)
    user.update(changes)
    return jsonify(user.to_dict()), 200


def delete_user(user_id):
    user = _get_user_or_404(user_id)
    user.delete()  # tasks removidas por cascade no relacionamento
    logger.info("Usuário deletado: %s", user_id)
    return jsonify({"message": MSG_USER_DELETED}), 200


def get_user_tasks(user_id):
    user = _get_user_or_404(user_id)
    result = []
    for task in user.tasks:
        data = task.to_dict(with_overdue=True)
        result.append({field: data[field] for field in USER_TASK_FIELDS})
    return jsonify(result), 200


def login():
    credentials = user_validator.validate_login(request.get_json(silent=True))
    user, token = auth_service.login(credentials["email"], credentials["password"])
    return jsonify({"message": MSG_LOGIN_OK, "user": user.to_dict(), "token": token}), 200
