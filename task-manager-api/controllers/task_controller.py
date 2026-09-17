from flask import jsonify, request

from errors import NotFoundError
from models.task import Task
from services import task_service
from validators import task_validator

MSG_TASK_NOT_FOUND = "Task não encontrada"
MSG_TASK_DELETED = "Task deletada com sucesso"


def _get_task_or_404(task_id):
    task = Task.get(task_id)
    if not task:
        raise NotFoundError(MSG_TASK_NOT_FOUND)
    return task


def list_tasks():
    result = [task.to_dict(with_overdue=True, with_names=True) for task in Task.list_all()]
    return jsonify(result), 200


def get_task(task_id):
    task = _get_task_or_404(task_id)
    return jsonify(task.to_dict(with_overdue=True)), 200


def create_task():
    payload = task_validator.validate_create(request.get_json(silent=True))
    task = task_service.create_task(payload)
    return jsonify(task.to_dict()), 201


def update_task(task_id):
    task = _get_task_or_404(task_id)
    changes = task_validator.validate_update(request.get_json(silent=True))
    task_service.update_task(task, changes)
    return jsonify(task.to_dict()), 200


def delete_task(task_id):
    task = _get_task_or_404(task_id)
    task_service.delete_task(task)
    return jsonify({"message": MSG_TASK_DELETED}), 200


def search_tasks():
    filters = task_validator.validate_search(request.args)
    result = [task.to_dict() for task in Task.search(**filters)]
    return jsonify(result), 200


def task_stats():
    by_status = Task.count_by_status()
    total = Task.count()
    done = by_status["done"]
    stats = {
        "total": total,
        **by_status,
        "overdue": Task.count_overdue(),
        "completion_rate": round((done / total) * 100, 2) if total > 0 else 0,
    }
    return jsonify(stats), 200
