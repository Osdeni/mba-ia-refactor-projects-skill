"""Task: persistência, regra de atraso, buscas/agregações e serializer."""
from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.orm import selectinload

from database import db
from utils.constants import (
    CLOSED_STATUSES,
    DEFAULT_PRIORITY,
    DEFAULT_STATUS,
    TAGS_SEPARATOR,
    VALID_STATUSES,
)
from utils.dates import format_date, utcnow

LIKE_ESCAPE = "\\"


def _escape_like(term):
    return term.replace(LIKE_ESCAPE, LIKE_ESCAPE * 2).replace("%", LIKE_ESCAPE + "%").replace("_", LIKE_ESCAPE + "_")


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=DEFAULT_STATUS)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship("User", back_populates="tasks")
    category = db.relationship("Category", back_populates="tasks")

    # --- invariantes ------------------------------------------------------------
    @property
    def tags_list(self):
        return self.tags.split(TAGS_SEPARATOR) if self.tags else []

    def is_overdue(self):
        return bool(self.due_date) and self.status not in CLOSED_STATUSES and self.due_date < utcnow()

    @classmethod
    def overdue_clause(cls):
        """Mesma regra de `is_overdue` como expressão SQL, para contagens sem carregar linhas."""
        return and_(cls.due_date.isnot(None), cls.due_date < utcnow(), cls.status.notin_(CLOSED_STATUSES))

    # --- serialização -------------------------------------------------------------
    def to_dict(self, with_overdue=False, with_names=False):
        data = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "user_id": self.user_id,
            "category_id": self.category_id,
            "created_at": str(self.created_at),
            "updated_at": str(self.updated_at),
            "due_date": format_date(self.due_date),
            "tags": self.tags_list,
        }
        if with_overdue:
            data["overdue"] = self.is_overdue()
        if with_names:
            data["user_name"] = self.user.name if self.user else None
            data["category_name"] = self.category.name if self.category else None
        return data

    # --- consultas ----------------------------------------------------------------
    @classmethod
    def get(cls, task_id):
        return db.session.get(cls, task_id)

    @classmethod
    def list_all(cls):
        stmt = select(cls).options(selectinload(cls.user), selectinload(cls.category)).order_by(cls.id)
        return db.session.scalars(stmt).all()

    @classmethod
    def for_user(cls, user_id):
        return db.session.scalars(select(cls).where(cls.user_id == user_id).order_by(cls.id)).all()

    @classmethod
    def search(cls, query=None, status=None, priority=None, user_id=None):
        stmt = select(cls)
        if query:
            pattern = f"%{_escape_like(query)}%"
            stmt = stmt.where(
                or_(cls.title.like(pattern, escape=LIKE_ESCAPE), cls.description.like(pattern, escape=LIKE_ESCAPE))
            )
        if status:
            stmt = stmt.where(cls.status == status)
        if priority is not None:
            stmt = stmt.where(cls.priority == priority)
        if user_id is not None:
            stmt = stmt.where(cls.user_id == user_id)
        return db.session.scalars(stmt.order_by(cls.id)).all()

    # --- agregações -------------------------------------------------------------------
    @classmethod
    def count(cls, *conditions):
        stmt = select(func.count()).select_from(cls)
        if conditions:
            stmt = stmt.where(*conditions)
        return db.session.scalar(stmt)

    @classmethod
    def count_by_status(cls):
        rows = db.session.execute(select(cls.status, func.count()).group_by(cls.status)).all()
        counts = dict(rows)
        return {status: counts.get(status, 0) for status in VALID_STATUSES}

    @classmethod
    def count_by_priority(cls):
        rows = db.session.execute(select(cls.priority, func.count()).group_by(cls.priority)).all()
        return dict(rows)

    @classmethod
    def count_overdue(cls):
        return cls.count(cls.overdue_clause())

    @classmethod
    def overdue_tasks(cls):
        return db.session.scalars(select(cls).where(cls.overdue_clause()).order_by(cls.id)).all()

    @classmethod
    def productivity_by_user(cls):
        """[(user_id, user_name, total, completed)] em uma query — sem loop por usuário."""
        from models.user import User

        completed = func.sum(case((cls.status == "done", 1), else_=0))
        stmt = (
            select(User.id, User.name, func.count(cls.id), completed)
            .outerjoin(cls, cls.user_id == User.id)
            .group_by(User.id)
            .order_by(User.id)
        )
        return db.session.execute(stmt).all()

    @classmethod
    def count_by_category(cls):
        rows = db.session.execute(select(cls.category_id, func.count()).group_by(cls.category_id)).all()
        return dict(rows)

    # --- persistência ---------------------------------------------------------------
    @classmethod
    def create(cls, payload):
        task = cls(**payload)
        db.session.add(task)
        db.session.commit()
        return task

    def update(self, changes):
        for field, value in changes.items():
            setattr(self, field, value)
        self.updated_at = utcnow()
        db.session.commit()
        return self

    def delete(self):
        db.session.delete(self)
        db.session.commit()
