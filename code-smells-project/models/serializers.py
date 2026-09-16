"""Serializadores whitelist: linha do banco → dict público (nunca expõem `senha`)."""

PRODUTO_FIELDS = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")
USUARIO_PUBLIC_FIELDS = ("id", "nome", "email", "tipo", "criado_em")
USUARIO_LOGIN_FIELDS = ("id", "nome", "email", "tipo")
PEDIDO_FIELDS = ("id", "usuario_id", "status", "total", "criado_em")
PRODUTO_DESCONHECIDO = "Desconhecido"


def _pick(row, fields):
    return {field: row[field] for field in fields}


def produto_to_dict(row):
    return _pick(row, PRODUTO_FIELDS)


def usuario_publico(row):
    return _pick(row, USUARIO_PUBLIC_FIELDS)


def usuario_login(row):
    return _pick(row, USUARIO_LOGIN_FIELDS)


def pedido_to_dict(row):
    pedido = _pick(row, PEDIDO_FIELDS)
    pedido["itens"] = []
    return pedido


def item_pedido_to_dict(row):
    return {
        "produto_id": row["produto_id"],
        "produto_nome": row["produto_nome"] or PRODUTO_DESCONHECIDO,
        "quantidade": row["quantidade"],
        "preco_unitario": row["preco_unitario"],
    }
