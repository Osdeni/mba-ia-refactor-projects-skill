"""Schema do banco (CREATE TABLE IF NOT EXISTS) com chaves estrangeiras e restrições."""

SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        descricao TEXT NOT NULL DEFAULT '',
        preco REAL NOT NULL CHECK (preco >= 0),
        estoque INTEGER NOT NULL CHECK (estoque >= 0),
        categoria TEXT NOT NULL DEFAULT 'geral',
        ativo INTEGER NOT NULL DEFAULT 1,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        senha TEXT NOT NULL,
        tipo TEXT NOT NULL DEFAULT 'cliente',
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
        status TEXT NOT NULL DEFAULT 'pendente',
        total REAL NOT NULL,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS itens_pedido (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
        produto_id INTEGER REFERENCES produtos(id) ON DELETE SET NULL,
        quantidade INTEGER NOT NULL CHECK (quantidade > 0),
        preco_unitario REAL NOT NULL
    )
    """,
)

# Ordem que respeita as chaves estrangeiras.
TABLES_IN_DELETE_ORDER = ("itens_pedido", "pedidos", "produtos", "usuarios")


def create_tables(conn):
    for statement in SCHEMA:
        conn.execute(statement)
    conn.commit()


def truncate_all(conn):
    """Apaga todos os registros (identificadores vêm de uma tupla fixa, nunca do cliente)."""
    for table in TABLES_IN_DELETE_ORDER:
        conn.execute(f"DELETE FROM {table}")
