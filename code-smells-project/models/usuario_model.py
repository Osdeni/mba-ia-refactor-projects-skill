"""Persistência de usuários. A senha (hash) só sai deste módulo via `buscar_credenciais`."""
from database.connection import get_db, transaction
from models.serializers import usuario_publico


def listar():
    rows = get_db().execute("SELECT * FROM usuarios ORDER BY id").fetchall()
    return [usuario_publico(row) for row in rows]


def buscar_por_id(usuario_id):
    row = get_db().execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    return usuario_publico(row) if row else None


def buscar_credenciais(email):
    """Uso exclusivo do serviço de autenticação: inclui o hash da senha."""
    row = get_db().execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
    if row is None:
        return None
    return {"id": row["id"], "nome": row["nome"], "email": row["email"], "tipo": row["tipo"], "senha": row["senha"]}


def email_existe(email):
    row = get_db().execute("SELECT 1 FROM usuarios WHERE email = ?", (email,)).fetchone()
    return row is not None


def criar(nome, email, senha_hash, tipo):
    with transaction() as conn:
        cursor = conn.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            (nome, email, senha_hash, tipo),
        )
        return cursor.lastrowid


def atualizar_senha(usuario_id, senha_hash):
    with transaction() as conn:
        conn.execute("UPDATE usuarios SET senha = ? WHERE id = ?", (senha_hash, usuario_id))


def contar():
    return get_db().execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
