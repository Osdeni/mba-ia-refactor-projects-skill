"""Persistência de produtos (queries parametrizadas)."""
from database.connection import get_db, transaction
from models.serializers import produto_to_dict


def listar():
    rows = get_db().execute("SELECT * FROM produtos ORDER BY id").fetchall()
    return [produto_to_dict(row) for row in rows]


def buscar_por_id(produto_id):
    row = get_db().execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
    return produto_to_dict(row) if row else None


def buscar(termo=None, categoria=None, preco_min=None, preco_max=None):
    clauses, params = ["1=1"], []
    if termo:
        clauses.append("(nome LIKE ? OR descricao LIKE ?)")
        params += [f"%{termo}%", f"%{termo}%"]
    if categoria:
        clauses.append("categoria = ?")
        params.append(categoria)
    if preco_min is not None:
        clauses.append("preco >= ?")
        params.append(preco_min)
    if preco_max is not None:
        clauses.append("preco <= ?")
        params.append(preco_max)
    sql = "SELECT * FROM produtos WHERE " + " AND ".join(clauses) + " ORDER BY id"
    rows = get_db().execute(sql, params).fetchall()
    return [produto_to_dict(row) for row in rows]


def criar(dados):
    with transaction() as conn:
        cursor = conn.execute(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            (dados["nome"], dados["descricao"], dados["preco"], dados["estoque"], dados["categoria"]),
        )
        return cursor.lastrowid


def atualizar(produto_id, dados):
    with transaction() as conn:
        cursor = conn.execute(
            "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
            (dados["nome"], dados["descricao"], dados["preco"], dados["estoque"], dados["categoria"], produto_id),
        )
        return cursor.rowcount > 0


def deletar(produto_id):
    with transaction() as conn:
        cursor = conn.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
        return cursor.rowcount > 0


def baixar_estoque(produto_id, quantidade):
    """Decremento atômico com guarda de estoque; retorna False se não havia estoque suficiente."""
    with transaction() as conn:
        cursor = conn.execute(
            "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
            (quantidade, produto_id, quantidade),
        )
        return cursor.rowcount == 1


def contar():
    return get_db().execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
