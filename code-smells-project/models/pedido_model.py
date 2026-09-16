"""Persistência de pedidos e itens (uma query com JOIN para listagens — sem N+1)."""
from database.connection import get_db, transaction
from models.serializers import item_pedido_to_dict, pedido_to_dict

_LISTAR_SQL = """
    SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
           i.id AS item_id, i.produto_id, i.quantidade, i.preco_unitario,
           pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = i.produto_id
    WHERE (? IS NULL OR p.usuario_id = ?)
    ORDER BY p.id, i.id
"""


def listar(usuario_id=None):
    rows = get_db().execute(_LISTAR_SQL, (usuario_id, usuario_id)).fetchall()
    pedidos = {}
    for row in rows:
        pedido = pedidos.get(row["id"])
        if pedido is None:
            pedido = pedidos[row["id"]] = pedido_to_dict(row)
        if row["item_id"] is not None:
            pedido["itens"].append(item_pedido_to_dict(row))
    return list(pedidos.values())


def existe(pedido_id):
    row = get_db().execute("SELECT 1 FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
    return row is not None


def criar(usuario_id, total, status):
    with transaction() as conn:
        cursor = conn.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
            (usuario_id, status, total),
        )
        return cursor.lastrowid


def adicionar_itens(pedido_id, itens):
    """`itens`: iterável de (produto_id, quantidade, preco_unitario)."""
    with transaction() as conn:
        conn.executemany(
            "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
            [(pedido_id, produto_id, quantidade, preco) for produto_id, quantidade, preco in itens],
        )


def atualizar_status(pedido_id, status):
    with transaction() as conn:
        cursor = conn.execute("UPDATE pedidos SET status = ? WHERE id = ?", (status, pedido_id))
        return cursor.rowcount > 0


def resumo_por_status():
    """{status: {"quantidade": n, "faturamento": soma}} em uma única query agregada."""
    rows = get_db().execute(
        "SELECT status, COUNT(*) AS quantidade, COALESCE(SUM(total), 0) AS faturamento FROM pedidos GROUP BY status"
    ).fetchall()
    return {row["status"]: {"quantidade": row["quantidade"], "faturamento": row["faturamento"]} for row in rows}


def contar():
    return get_db().execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
