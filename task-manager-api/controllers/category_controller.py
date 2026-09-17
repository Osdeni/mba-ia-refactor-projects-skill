from flask import jsonify, request

from errors import NotFoundError
from models.category import Category
from models.task import Task
from validators import category_validator

MSG_CATEGORY_NOT_FOUND = "Categoria não encontrada"
MSG_CATEGORY_DELETED = "Categoria deletada"


def _get_category_or_404(category_id):
    category = Category.get(category_id)
    if not category:
        raise NotFoundError(MSG_CATEGORY_NOT_FOUND)
    return category


def list_categories():
    counts = Task.count_by_category()
    result = [{**category.to_dict(), "task_count": counts.get(category.id, 0)} for category in Category.list_all()]
    return jsonify(result), 200


def create_category():
    payload = category_validator.validate_create(request.get_json(silent=True))
    category = Category.create(payload)
    return jsonify(category.to_dict()), 201


def update_category(category_id):
    category = _get_category_or_404(category_id)
    changes = category_validator.validate_update(request.get_json(silent=True))
    category.update(changes)
    return jsonify(category.to_dict()), 200


def delete_category(category_id):
    category = _get_category_or_404(category_id)
    category.delete()  # tasks vinculadas ficam com category_id = NULL
    return jsonify({"message": MSG_CATEGORY_DELETED}), 200
