"""Categoria: persistência e serializer."""
from sqlalchemy import func, select

from database import db
from utils.constants import DEFAULT_COLOR
from utils.dates import utcnow


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    color = db.Column(db.String(7), default=DEFAULT_COLOR)
    created_at = db.Column(db.DateTime, default=utcnow)

    # Sem cascade de delete: ao apagar a categoria, o ORM anula `category_id` das tasks.
    tasks = db.relationship("Task", back_populates="category")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "created_at": str(self.created_at),
        }

    @classmethod
    def get(cls, category_id):
        return db.session.get(cls, category_id)

    @classmethod
    def list_all(cls):
        return db.session.scalars(select(cls).order_by(cls.id)).all()

    @classmethod
    def count(cls):
        return db.session.scalar(select(func.count()).select_from(cls))

    @classmethod
    def create(cls, payload):
        category = cls(**payload)
        db.session.add(category)
        db.session.commit()
        return category

    def update(self, changes):
        for field, value in changes.items():
            setattr(self, field, value)
        db.session.commit()
        return self

    def delete(self):
        db.session.delete(self)
        db.session.commit()
