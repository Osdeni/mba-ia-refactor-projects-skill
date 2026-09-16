# 05 — Refactoring Playbook (Phase 3)

Each pattern: **Fixes** (catalog IDs) · **When** · **Before / After** in Python (Flask) and
JavaScript (Express) · **Contract notes**. Apply the patterns that map to the audit findings, in
the order given in SKILL.md. Examples are minimal — adapt names to the project's domain language.

---

## P1 — Extract configuration to an env-backed module
**Fixes:** AP-01, AP-10. **When:** any literal secret/host/port/db path/debug flag in source.

Python — before:
```python
app = Flask(__name__)
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
CORS(app)
app.run(host="0.0.0.0", port=5000, debug=True)
```
Python — after (`config/settings.py`):
```python
import os, logging

def _bool(name, default): return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes")

SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
DEBUG = _bool("DEBUG", False)
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "5000"))
DB_PATH = os.getenv("DB_PATH", "loja.db")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")            # None → admin routes answer 403
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
if SECRET_KEY == "dev-only-change-me":
    logging.getLogger(__name__).warning("SECRET_KEY default in use — set it in the environment")
```
```python
# app.py
from config import settings
def create_app():
    app = Flask(__name__)
    app.config.from_object(settings)
    CORS(app, origins=settings.CORS_ORIGINS)
    ...
    return app
app = create_app()
if __name__ == "__main__":
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
```

JS — before (`utils.js`):
```js
const config = { dbPass: "senha_super_secreta_prod_123", paymentGatewayKey: "pk_live_1234567890abcdef", port: 3000 };
```
JS — after (`config/index.js`):
```js
const config = Object.freeze({
  env: process.env.NODE_ENV || "development",
  port: Number(process.env.PORT) || 3000,
  dbFile: process.env.DB_FILE || ":memory:",
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || "pk_test_dev_only",
  adminToken: process.env.ADMIN_TOKEN || null,
  logLevel: process.env.LOG_LEVEL || "info",
});
module.exports = config;
```
Ship `.env.example` listing every key. **Contract:** defaults reproduce the original port and DB
so the run command keeps working with no `.env`.

---

## P2 — Parameterised queries
**Fixes:** AP-02. **When:** any SQL built with `+`, f-strings, `%`, `.format`, template literals.

Python — before:
```python
cursor.execute("SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'")
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
```
Python — after:
```python
cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))       # password checked in code (P4)
cursor.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,))
# dynamic filters
clauses, params = ["1=1"], []
if termo is not None:      clauses.append("(nome LIKE ? OR descricao LIKE ?)"); params += [f"%{termo}%"] * 2
if preco_min is not None:  clauses.append("preco >= ?"); params.append(preco_min)
cursor.execute(f"SELECT * FROM produtos WHERE {' AND '.join(clauses)}", params)   # only fixed fragments joined
```
JS — before / after:
```js
db.get(`SELECT * FROM courses WHERE id = ${cid}`, cb);          // before
await db.get("SELECT * FROM courses WHERE id = ? AND active = 1", [courseId]);   // after
```
Identifiers (table/column/sort) can never be parameters — validate them against a whitelist.

---

## P3 — Decompose a god module into MVC layers
**Fixes:** AP-03, AP-07. **When:** one file/class owns DB + rules + routing.

Python — before: `models.py` (4 domains, SQL + validation + dict formatting), `controllers.py`
(15 handlers), `app.py` (17 `add_url_rule` + inline `/admin/*` running SQL).
Python — after:
```
models/produto_model.py      # listar(), buscar_por_id(), criar(), atualizar(), deletar()  (parameterised)
models/serializers.py        # produto_to_dict(row), usuario_publico(row)
services/pedido_service.py   # criar_pedido(usuario_id, itens) with stock check + transaction
controllers/produto_controller.py
routes/produto_routes.py     # bp = Blueprint("produtos", __name__); bp.get("/produtos")(controller.listar)
routes/__init__.py           # register_blueprints(app)
app.py                       # create_app() composition root only
```
```python
# routes/produto_routes.py
from flask import Blueprint
from controllers import produto_controller as c
bp = Blueprint("produtos", __name__)
bp.add_url_rule("/produtos", "listar", c.listar, methods=["GET"])
bp.add_url_rule("/produtos/<int:produto_id>", "buscar", c.buscar, methods=["GET"])
```
JS — before: `AppManager` class = `initDb()` + `setupRoutes(app)` with 3 inline route bodies.
JS — after:
```
database/{connection,schema,seed}.js   services/checkoutService.js   controllers/checkoutController.js
routes/checkoutRoutes.js               routes/index.js (mounts /api)  app.js (composition root)
```
```js
// routes/checkoutRoutes.js
const router = require("express").Router();
const { checkout } = require("../controllers/checkoutController");
const asyncHandler = require("../middlewares/asyncHandler");
router.post("/checkout", asyncHandler(checkout));
module.exports = router;
```
Delete the old flat modules in the same step and grep for stale imports.

---

## P4 — Real password hashing with legacy verify-and-upgrade
**Fixes:** AP-04. **When:** plaintext, MD5/SHA1 or home-made hashes.

Python — before:
```python
self.password = hashlib.md5(pwd.encode()).hexdigest()
def check_password(self, pwd): return self.password == hashlib.md5(pwd.encode()).hexdigest()
```
Python — after (`werkzeug.security` ships with Flask — no new dependency):
```python
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib, hmac

def hash_password(raw): return generate_password_hash(raw)

def verify_password(stored, raw):
    """Returns (ok, needs_upgrade). Accepts modern hashes, legacy MD5 and plaintext."""
    if stored.startswith(("scrypt:", "pbkdf2:")):
        return check_password_hash(stored, raw), False
    if len(stored) == 32 and all(c in "0123456789abcdef" for c in stored):       # legacy md5
        return hmac.compare_digest(stored, hashlib.md5(raw.encode()).hexdigest()), True
    return hmac.compare_digest(stored, raw), True                               # legacy plaintext
```
On successful legacy login: re-hash and `UPDATE` the row (transparent upgrade). Seeds use
`hash_password(...)` so fresh DBs are clean and existing DB files keep working.

JS — before: `badCrypto(pwd)` (base64 truncated). JS — after (`utils/crypto.js`, no new deps):
```js
const { scryptSync, randomBytes, timingSafeEqual } = require("crypto");
function hashPassword(pwd) { const salt = randomBytes(16).toString("hex");
  return `scrypt$${salt}$${scryptSync(pwd, salt, 32).toString("hex")}`; }
function verifyPassword(stored, pwd) {
  if (!stored.startsWith("scrypt$")) return timingSafeEqual(Buffer.from(stored), Buffer.from(pwd)); // legacy
  const [, salt, hash] = stored.split("$");
  return timingSafeEqual(Buffer.from(hash, "hex"), scryptSync(pwd, salt, 32)); }
```

---

## P5 — Whitelist serializers and log redaction
**Fixes:** AP-05. **When:** responses/logs contain passwords, secrets, cards, PII.

Python — before:
```python
def to_dict(self): return {"id": self.id, "email": self.email, "password": self.password, ...}
return jsonify({"status": "ok", "secret_key": app.config["SECRET_KEY"], "debug": True, "db_path": DB_PATH})
```
Python — after:
```python
PUBLIC_FIELDS = ("id", "name", "email", "role", "created_at")
def to_dict(self): return {f: _json(getattr(self, f)) for f in PUBLIC_FIELDS}
return jsonify({"status": "ok", "versao": VERSION, "banco": {"produtos": n_p, "usuarios": n_u}})
```
JS — before: ``console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`)``
JS — after: ``logger.info(`Processing card ${maskCard(card)}`)`` with
`maskCard = c => "****" + String(c).slice(-4)`; never log keys/tokens.

---

## P6 — Admin-token guard for privileged endpoints
**Fixes:** AP-06. **When:** admin/destructive/raw-SQL endpoints are public.

Python — after (`middlewares/auth.py`):
```python
import hmac
from functools import wraps
from flask import request
from config import settings
from errors import ForbiddenError, UnauthorizedError

def require_admin(fn):
    @wraps(fn)
    def wrapper(*a, **kw):
        if not settings.ADMIN_TOKEN: raise ForbiddenError("Rotas administrativas desabilitadas (ADMIN_TOKEN não configurado)")
        token = request.headers.get("X-Admin-Token", "")
        if not hmac.compare_digest(token, settings.ADMIN_TOKEN): raise UnauthorizedError("Token administrativo inválido")
        return fn(*a, **kw)
    return wrapper
```
Raw-SQL endpoint: keep the route, allow only `^\s*SELECT\b` (reject the rest with 400), execute on
a read-only connection (`sqlite3.connect(f"file:{path}?mode=ro", uri=True)`).

JS — after (`middlewares/requireAdmin.js`):
```js
module.exports = (req, res, next) => {
  if (!config.adminToken) return next(new AppError(403, "Admin routes disabled"));
  if (req.get("X-Admin-Token") !== config.adminToken) return next(new AppError(401, "Invalid admin token"));
  next(); };
```
**Contract:** routes still exist; document the header in README/`api.http`; validation sends it.

---

## P7 — Thin controller + service extraction
**Fixes:** AP-07. **When:** handlers > 30 lines mixing validation, rules, persistence, notifications.

Python — before (`controllers.py`):
```python
def criar_pedido():
    dados = request.get_json()
    ...30 lines: validation, stock loop, total, insert, print("EMAIL enviado")...
```
Python — after:
```python
# controllers/pedido_controller.py
def criar():
    dados = request.get_json(silent=True) or {}
    payload = pedido_validator.validar_criacao(dados)          # raises ValidationError(400, msg)
    pedido = pedido_service.criar_pedido(payload["usuario_id"], payload["itens"])
    return jsonify({"dados": pedido, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201

# services/pedido_service.py
def criar_pedido(usuario_id, itens):
    with transaction() as conn:
        total = 0
        for item in itens:
            produto = produto_model.buscar_por_id(item["produto_id"], conn) or _raise(NotFoundError(...))
            if produto["estoque"] < item["quantidade"]: raise ValidationError(f"Estoque insuficiente para {produto['nome']}")
            total += produto["preco"] * item["quantidade"]
        pedido_id = pedido_model.inserir(conn, usuario_id, total, itens)
        produto_model.baixar_estoque(conn, itens)
    notificacao_service.pedido_criado(pedido_id, usuario_id)   # logger, not print
    return pedido_model.buscar_por_id(pedido_id)
```
JS — before: 50-line checkout closure. JS — after:
```js
// controllers/checkoutController.js
async function checkout(req, res) {
  const input = validateCheckout(req.body);                       // throws AppError(400, "Bad Request")
  const { enrollmentId } = await checkoutService.checkout(input);
  res.status(200).json({ msg: "Sucesso", enrollment_id: enrollmentId });
}
// services/checkoutService.js: findActiveCourse → findOrCreateUser → paymentGateway.charge → withTransaction(enroll + pay + audit)
```
**Contract:** same status codes and messages (`"Bad Request"`, `"Curso não encontrado"`, `"Pagamento recusado"`).

---

## P8 — Scoped database access instead of globals
**Fixes:** AP-08, AP-11. **When:** module-level connection, `check_same_thread=False`, `new Database()` in constructors.

Python — before:
```python
db_connection = None
def get_db():
    global db_connection
    if db_connection is None: db_connection = sqlite3.connect(DB_PATH, check_same_thread=False); ...create tables, seed...
    return db_connection
```
Python — after (`database/connection.py`):
```python
import sqlite3
from contextlib import contextmanager
from flask import g
from config import settings

def _connect():
    conn = sqlite3.connect(settings.DB_PATH); conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON"); return conn

def get_db():
    if "db" not in g: g.db = _connect()
    return g.db

def close_db(_=None):
    conn = g.pop("db", None)
    if conn is not None: conn.close()

@contextmanager
def transaction():
    conn = get_db()
    try: yield conn; conn.commit()
    except Exception: conn.rollback(); raise

def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context(): schema.create_tables(_connect()); seed.run_if_empty(_connect())
```
ORM projects: keep `db = SQLAlchemy()` in `database.py`, create the app with a factory and call
`db.init_app(app)` there; never `create_all()` at import time of a routes module.

JS — after (`database/connection.js`):
```js
const sqlite3 = require("sqlite3");
const db = new sqlite3.Database(config.dbFile);
const run = (sql, p = []) => new Promise((res, rej) => db.run(sql, p, function (e) { e ? rej(e) : res({ lastID: this.lastID, changes: this.changes }); }));
const get = (sql, p = []) => new Promise((res, rej) => db.get(sql, p, (e, r) => (e ? rej(e) : res(r))));
const all = (sql, p = []) => new Promise((res, rej) => db.all(sql, p, (e, r) => (e ? rej(e) : res(r))));
async function withTransaction(fn) { await run("BEGIN"); try { const r = await fn(); await run("COMMIT"); return r; } catch (e) { await run("ROLLBACK"); throw e; } }
module.exports = { run, get, all, withTransaction, raw: db };
```
Delete `globalCache`/`totalRevenue`-style exports that nothing reads.

---

## P9 — Centralized error handling
**Fixes:** AP-09. **When:** repeated try/except, bare `except:`, no error middleware.

Python — before (×15):
```python
try: ...
except Exception as e: return jsonify({"erro": str(e)}), 500
```
Python — after:
```python
# errors.py
class AppError(Exception):
    status = 500
    def __init__(self, message, status=None): super().__init__(message); self.message = message; self.status = status or self.status
class ValidationError(AppError): status = 400
class NotFoundError(AppError): status = 404
class UnauthorizedError(AppError): status = 401
class ForbiddenError(AppError): status = 403

# middlewares/error_handler.py
from werkzeug.exceptions import HTTPException
def register_error_handlers(app, envelope="erro"):
    @app.errorhandler(AppError)
    def _app(e): return jsonify({envelope: e.message, "sucesso": False}), e.status
    @app.errorhandler(HTTPException)
    def _http(e): return jsonify({envelope: e.description, "sucesso": False}), e.code
    @app.errorhandler(Exception)
    def _any(e): app.logger.exception("Unhandled error"); return jsonify({envelope: "Erro interno", "sucesso": False}), 500
```
Controllers raise `NotFoundError("Produto não encontrado")` instead of building responses by hand.

JS — after:
```js
// errors/AppError.js
class AppError extends Error { constructor(status, message) { super(message); this.status = status; } }
// middlewares/asyncHandler.js
module.exports = fn => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);
// middlewares/errorHandler.js  (registered AFTER routes)
module.exports = (err, req, res, next) => {
  if (err.type === "entity.parse.failed") return res.status(400).send("Bad Request");
  const status = err.status || 500;
  if (status >= 500) logger.error(err);
  res.status(status).send(status >= 500 ? "Erro interno" : err.message);   // text envelope kept
};
// middlewares/notFound.js
module.exports = (req, res) => res.status(404).send("Not Found");
```

---

## P10 — Callback pyramid → async/await (and guard clauses)
**Fixes:** AP-11 (JS), AP-19 (nesting). **When:** ≥3 nested callbacks or 4-level if/else.

JS — before:
```js
this.db.get(sqlCourse, [cid], (err, course) => { if (err || !course) return res.status(404)...;
  this.db.get(sqlUser, [e], (err, user) => { ... this.db.run(insertEnr, ..., function (err) { ... }) }) });
```
JS — after:
```js
async function checkout({ name, email, password, courseId, card }) {
  const course = await courseModel.findActive(courseId);
  if (!course) throw new AppError(404, "Curso não encontrado");
  const user = (await userModel.findByEmail(email)) || (await userModel.create({ name, email, password }));
  const status = paymentGateway.charge(card);
  if (status === PAYMENT_STATUS.DENIED) throw new AppError(400, "Pagamento recusado");
  return withTransaction(async () => {
    const enrollmentId = await enrollmentModel.create(user.id, course.id);
    await paymentModel.create(enrollmentId, course.price, status);
    await auditLogModel.record(`Checkout curso ${course.id} por ${user.id}`);
    return { enrollmentId };
  });
}
```
Python — nested booleans → guard clauses:
```python
def is_overdue(self):                       # before: 4 nested ifs returning True/False
    return bool(self.due_date) and self.status not in ("done", "cancelled") and self.due_date < utcnow_naive()
```

---

## P11 — Eliminate N+1 queries
**Fixes:** AP-12. **When:** query inside a loop, per-row lookups, lazy collection counts.

Python (sqlite3) — before:
```python
for pedido in pedidos:
    cursor.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(pedido["id"]))
    for item in cursor.fetchall():
        cursor.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))
```
Python — after:
```python
rows = conn.execute("""
    SELECT p.id, p.usuario_id, p.total, p.status, p.data_criacao,
           i.produto_id, i.quantidade, i.preco_unitario, pr.nome AS produto_nome
    FROM pedidos p LEFT JOIN itens_pedido i ON i.pedido_id = p.id
                   LEFT JOIN produtos pr ON pr.id = i.produto_id
    WHERE (? IS NULL OR p.usuario_id = ?) ORDER BY p.id""", (usuario_id, usuario_id)).fetchall()
pedidos = {}
for r in rows:
    pedido = pedidos.setdefault(r["id"], {"id": r["id"], ..., "itens": []})
    if r["produto_id"] is not None: pedido["itens"].append({...})
```
Python (SQLAlchemy) — before/after:
```python
for t in Task.query.all(): user = User.query.get(t.user_id)                    # before
tasks = db.session.scalars(select(Task).options(selectinload(Task.user), selectinload(Task.category))).all()   # after
counts = dict(db.session.execute(select(Task.user_id, func.count()).group_by(Task.user_id)).all())            # task_count
```
JS — before: courses → per course enrollments → per enrollment user + payment. JS — after:
```js
const rows = await db.all(`
  SELECT c.title AS course, u.name AS student, p.amount, p.status
  FROM courses c LEFT JOIN enrollments e ON e.course_id = c.id
                 LEFT JOIN users u ON u.id = e.user_id
                 LEFT JOIN payments p ON p.enrollment_id = e.id
  ORDER BY c.id, e.id`);
// reduce into [{ course, revenue, students: [{ student, paid }] }] preserving the original shape
```

---

## P12 — Validators and serializers as single sources of truth
**Fixes:** AP-13, AP-15. **When:** duplicated checks, divergent create/update, unguarded input.

Python — after (`validators/produto_validator.py`):
```python
from errors import ValidationError
from constants import CATEGORIAS_VALIDAS

def validar(dados, partial=False):
    if not isinstance(dados, dict) or not dados: raise ValidationError("Dados não informados")
    out = {}
    if "nome" in dados or not partial:
        nome = str(dados.get("nome", "")).strip()
        if len(nome) < 3: raise ValidationError("Nome deve ter pelo menos 3 caracteres")
        out["nome"] = nome
    if "preco" in dados or not partial:
        preco = dados.get("preco")
        if not isinstance(preco, (int, float)) or isinstance(preco, bool) or preco < 0: raise ValidationError("Preço inválido")
        out["preco"] = float(preco)
    ...
    return out
```
Use the **original error messages** so the contract is preserved; `partial=True` for PUT.
`request.get_json(silent=True) or {}` everywhere (never let Flask raise 415 into a 500).

JS — after (`validators/checkoutValidator.js`):
```js
function validateCheckout(body = {}) {
  const { usr, eml, pwd, c_id, card } = body;
  if (!usr || !eml || !c_id || !card) throw new AppError(400, "Bad Request");
  if (typeof card !== "string") throw new AppError(400, "Bad Request");
  return { name: usr, email: eml, password: pwd, courseId: Number(c_id), card };
}
```

---

## P13 — Modernize deprecated APIs
**Fixes:** AP-14. **When:** any row of the catalog's deprecated table matches.

Python:
```python
# before                               # after
datetime.utcnow()                      datetime.now(timezone.utc)            # or utcnow_naive() = datetime.now(timezone.utc).replace(tzinfo=None) when columns are naive
Task.query.get(task_id)                db.session.get(Task, task_id)
Task.query.filter_by(status=s).all()   db.session.scalars(select(Task).filter_by(status=s)).all()
Task.query.count()                     db.session.scalar(select(func.count()).select_from(Task))
request.get_json()                     request.get_json(silent=True) or {}
hashlib.md5(pwd)                       generate_password_hash(pwd)  (+ legacy verify, P4)
app.run(debug=True)                    app.run(debug=settings.DEBUG) + document gunicorn for prod
SQLALCHEMY_TRACK_MODIFICATIONS=False   (remove — default)
```
Keep serialized datetime strings identical when clients depend on them: store naive UTC
(`.replace(tzinfo=None)`) so `str(created_at)` does not gain `+00:00`.

JS:
```js
// before                                  // after
db.get(sql, params, (err, row) => {...})   const row = await db.get(sql, params)   (promisified wrapper, P8)
new Buffer(str)                            Buffer.from(str)
bodyParser.json()                          express.json()
str.substr(0, 10)                          str.slice(0, 10)
app.del("/x")                              app.delete("/x")
```
Express 4 stays acceptable if `asyncHandler` is used; mention Express 5 in README as an upgrade path.

---

## P14 — Data integrity: foreign keys, cascades, transactions
**Fixes:** AP-16. **When:** orphans, partial writes, manual delete loops.

Python (sqlite3) — after:
```sql
CREATE TABLE IF NOT EXISTS itens_pedido (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  pedido_id INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
  produto_id INTEGER NOT NULL REFERENCES produtos(id),
  quantidade INTEGER NOT NULL CHECK (quantidade > 0), preco_unitario REAL NOT NULL);
```
`PRAGMA foreign_keys = ON` on every connection; multi-step writes inside `with transaction():`;
stock decrement as an atomic guard: `UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?` and check `rowcount`.

Python (SQLAlchemy) — before: manual loop deleting tasks then the user. After:
```python
tasks = db.relationship("Task", backref="user", lazy=True, cascade="all, delete-orphan")
```
Category delete: `UPDATE tasks SET category_id = NULL` (or cascade) before removing the category.

JS — after: `withTransaction` (P8) around enroll + pay + audit; `DELETE /api/users/:id` removes
payments → enrollments → user inside one transaction and returns `"Usuário deletado"` (status 200 kept).

---

## P15 — Readability bundle: constants, naming, logger, dead code
**Fixes:** AP-17, AP-18, AP-19. **When:** always, as the last pass.

Python:
```python
# constants.py
CATEGORIAS_VALIDAS = ("eletronicos", "informatica", "livros", "roupas", "geral")
STATUS_PEDIDO = ("pendente", "aprovado", "enviado", "entregue", "cancelado")
FAIXAS_DESCONTO = ((10000, 0.10), (5000, 0.05), (1000, 0.02))
VERSION = "1.0.0"
# utils/logger.py
import logging; from config import settings
logging.basicConfig(level=settings.LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
def get_logger(name): return logging.getLogger(name)
```
Rename `id` → `produto_id`, `t/u/c` → `task/user/category`; keep external JSON keys unchanged.
Delete unused imports, unused helpers and modules with zero references (verify with grep);
`type(x) == list` → `isinstance(x, list)`; `x = x + 1` → `x += 1`.

JS:
```js
// utils/constants.js
module.exports = Object.freeze({ PAYMENT_STATUS: { PAID: "PAID", DENIED: "DENIED" }, CARD_APPROVED_PREFIX: "4" });
// utils/logger.js — minimal leveled logger over console, no PII
```
Rename `usr/eml/pwd/cid/cc` internally (`name/email/password/courseId/card`) while still reading
`req.body.usr` etc. in the validator; drop `const self = this`; `let` → `const`.
