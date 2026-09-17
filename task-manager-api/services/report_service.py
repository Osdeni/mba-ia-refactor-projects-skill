"""Relatórios: agregações multi-model feitas em SQL (sem loops de queries)."""
from datetime import timedelta

from models.category import Category
from models.task import Task
from models.user import User
from utils.constants import HIGH_PRIORITY_MAX, PRIORITY_LABELS, RECENT_DAYS
from utils.dates import utcnow


def _percentage(part, total):
    return round((part / total) * 100, 2) if total > 0 else 0


def _overdue_entries(now):
    return [
        {
            "id": task.id,
            "title": task.title,
            "due_date": str(task.due_date),
            "days_overdue": (now - task.due_date).days,
        }
        for task in Task.overdue_tasks()
    ]


def summary():
    now = utcnow()
    since = now - timedelta(days=RECENT_DAYS)
    by_status = Task.count_by_status()
    by_priority = Task.count_by_priority()
    overdue = _overdue_entries(now)

    user_productivity = [
        {
            "user_id": user_id,
            "user_name": user_name,
            "total_tasks": total,
            "completed_tasks": int(completed or 0),
            "completion_rate": _percentage(int(completed or 0), total),
        }
        for user_id, user_name, total, completed in Task.productivity_by_user()
    ]

    return {
        "generated_at": str(now),
        "overview": {
            "total_tasks": Task.count(),
            "total_users": User.count(),
            "total_categories": Category.count(),
        },
        "tasks_by_status": by_status,
        "tasks_by_priority": {label: by_priority.get(level, 0) for level, label in PRIORITY_LABELS.items()},
        "overdue": {"count": len(overdue), "tasks": overdue},
        "recent_activity": {
            "tasks_created_last_7_days": Task.count(Task.created_at >= since),
            "tasks_completed_last_7_days": Task.count(Task.status == "done", Task.updated_at >= since),
        },
        "user_productivity": user_productivity,
    }


def user_report(user):
    tasks = Task.for_user(user.id)
    total = len(tasks)
    by_status = {status: 0 for status in Task.count_by_status()}
    for task in tasks:
        if task.status in by_status:
            by_status[task.status] += 1

    return {
        "user": {"id": user.id, "name": user.name, "email": user.email},
        "statistics": {
            "total_tasks": total,
            "done": by_status["done"],
            "pending": by_status["pending"],
            "in_progress": by_status["in_progress"],
            "cancelled": by_status["cancelled"],
            "overdue": sum(1 for task in tasks if task.is_overdue()),
            "high_priority": sum(1 for task in tasks if task.priority <= HIGH_PRIORITY_MAX),
            "completion_rate": _percentage(by_status["done"], total),
        },
    }
