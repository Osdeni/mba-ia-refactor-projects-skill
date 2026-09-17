"""Usuário: persistência, invariantes de credencial e serializer público."""
import hashlib
import hmac

from sqlalchemy import func, select
from werkzeug.security import check_password_hash, generate_password_hash

from database import db
from utils.constants import DEFAULT_ROLE
from utils.dates import utcnow

_MODERN_HASH_PREFIXES = ("scrypt:", "pbkdf2:")


def _looks_like_md5(value):
    return len(value) == 32 and all(c in "0123456789abcdef" for c in value)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=DEFAULT_ROLE)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    tasks = db.relationship("Task", back_populates="user", cascade="all, delete-orphan")

    # --- serialização (whitelist: nunca expõe `password`) -------------------
    def to_dict(self, with_tasks=False):
        data = {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "active": self.active,
            "created_at": str(self.created_at),
        }
        if with_tasks:
            data["tasks"] = [task.to_dict() for task in self.tasks]
        return data

    # --- credenciais ----------------------------------------------------------
    @staticmethod
    def hash_password(raw):
        return generate_password_hash(raw)

    def set_password(self, raw):
        self.password = self.hash_password(raw)

    def verify_password(self, raw):
        """Retorna (ok, precisa_upgrade). Aceita hash moderno, MD5 legado e texto puro legado."""
        stored = self.password or ""
        if stored.startswith(_MODERN_HASH_PREFIXES):
            return check_password_hash(stored, raw), False
        if _looks_like_md5(stored):
            legacy = hashlib.md5(raw.encode(), usedforsecurity=False).hexdigest()
            return hmac.compare_digest(stored, legacy), True
        return hmac.compare_digest(stored, raw), True

    def check_password(self, raw):
        return self.verify_password(raw)[0]

    def is_admin(self):
        return self.role == "admin"

    # --- consultas ------------------------------------------------------------
    @classmethod
    def get(cls, user_id):
        return db.session.get(cls, user_id)

    @classmethod
    def get_by_email(cls, email):
        return db.session.scalar(select(cls).where(cls.email == email))

    @classmethod
    def list_with_task_counts(cls):
        """[(User, task_count)] em uma única query (evita N+1 em `len(user.tasks)`)."""
        from models.task import Task

        stmt = (
            select(cls, func.count(Task.id))
            .outerjoin(Task, Task.user_id == cls.id)
            .group_by(cls.id)
            .order_by(cls.id)
        )
        return db.session.execute(stmt).all()

    @classmethod
    def count(cls):
        return db.session.scalar(select(func.count()).select_from(cls))

    # --- persistência ---------------------------------------------------------
    @classmethod
    def create(cls, name, email, password, role=DEFAULT_ROLE):
        user = cls(name=name, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    def update(self, changes):
        for field, value in changes.items():
            if field == "password":
                self.set_password(value)
            else:
                setattr(self, field, value)
        db.session.commit()
        return self

    def delete(self):
        db.session.delete(self)
        db.session.commit()
