# 04 — MVC Architecture Guidelines (Phase 3 target)

## 1. Layers and responsibilities

| Layer | Owns | Must NOT |
|---|---|---|
| **Config** (`config/`) | reading environment variables with safe defaults; constants derived from env | import anything from the app |
| **Models** (`models/`) | persistence per entity (queries/ORM), invariants, domain helpers (`is_overdue`, `verify_password`), serializers (whitelisted `to_dict`) | touch `request`/`response`, print, decide HTTP codes |
| **Services** (`services/`) | multi-model use-cases, transactions, external gateways (payment, e-mail), reports/aggregations | know about HTTP |
| **Controllers** (`controllers/`) | parse request → call validator → call service/model → build response (status + body) | contain SQL/ORM queries, business rules, notification side effects |
| **Views / Routes** (`routes/`) | URL → controller mapping only (blueprints / routers), URL prefixes | contain logic beyond delegation |
| **Middlewares** (`middlewares/`) | cross-cutting: centralized error handler, 404, auth guard, request logging, CORS policy | domain logic |
| **Validators** (`validators/`) | input validation returning the project's existing error messages | persistence |
| **Database** (`database/`) | connection lifecycle (scoped), schema creation/migrations, seeds, transaction helper | business rules |
| **Entry point / composition root** (`app.py`, `src/app.js`) | create app, load config, register middlewares + routes, start server | define routes inline, run SQL |

Dependency direction (never upward): `routes → controllers → services → models → database`;
`config`, `errors`, `constants`, `utils/logger` may be imported by any layer.
Only controllers/routes/middlewares may import the framework's request/response objects.

## 2. Naming conventions

- Python: `models/produto_model.py`, `controllers/produto_controller.py`,
  `routes/produto_routes.py`, `services/pedido_service.py`, `validators/produto_validator.py`,
  `middlewares/error_handler.py`, `config/settings.py`, `errors.py`, `constants.py`.
- Node: `models/userModel.js`, `controllers/checkoutController.js`, `routes/checkoutRoutes.js`,
  `services/checkoutService.js`, `middlewares/errorHandler.js`, `config/index.js`,
  `errors/AppError.js`, `utils/logger.js`, `utils/constants.js`.
- Keep the project's domain language for entity names (`produto`, `pedido`, `task`, `course`).

## 3. Per-stack target layouts

### Python / Flask (packages at project root; entry point stays `app.py`)
```
app.py                     # create_app() + module-level app (keeps `python app.py` and `from app import app` working)
config/settings.py         # env-backed settings with defaults
database/connection.py     # get_db() via flask.g + teardown  (sqlite3)  |  database.py with db = SQLAlchemy() (ORM projects)
database/schema.py         # CREATE TABLE IF NOT EXISTS (+FK)          |  (ORM: models define schema)
database/seed.py           # seeds (hashed passwords)                   |  seed.py kept at root if it already exists
models/<entity>_model.py   # or models/<entity>.py for ORM classes
models/serializers.py      # row/model → public dict
services/<usecase>_service.py
controllers/<entity>_controller.py
routes/__init__.py         # register_blueprints(app)
routes/<entity>_routes.py  # Blueprint with url rules only
middlewares/error_handler.py, middlewares/auth.py
validators/<entity>_validator.py
errors.py, constants.py, .env.example
```
Flask specifics: use Blueprints; `create_app(config=None)` registers CORS from `CORS_ORIGINS`,
blueprints, error handlers; `if __name__ == "__main__": app.run(host=settings.HOST,
port=settings.PORT, debug=settings.DEBUG)`. Keep endpoint function names unique per blueprint.

### Node / Express (keep `src/`; entry point stays `src/app.js`, `npm start` unchanged)
```
src/app.js                 # composition root: express.json(), routes, notFound, errorHandler, listen(config.port); module.exports = app
src/config/index.js        # process.env with defaults, Object.freeze
src/database/connection.js # sqlite3 instance + promisified get/all/run/exec + withTransaction
src/database/schema.js     # CREATE TABLE ... FOREIGN KEY ... ON DELETE CASCADE
src/database/seed.js
src/models/<entity>Model.js
src/services/<usecase>Service.js, src/services/paymentGateway.js
src/controllers/<entity>Controller.js
src/routes/index.js (mounts prefixes), src/routes/<entity>Routes.js (express.Router)
src/middlewares/errorHandler.js, notFound.js, asyncHandler.js, requireAdmin.js
src/errors/AppError.js, src/utils/logger.js, src/utils/crypto.js, src/utils/constants.js
.env.example
```
Express specifics: wrap async controllers with `asyncHandler` (Express 4 does not propagate
rejected promises); register `notFound` then the 4-arg `errorHandler` **after** all routes;
`app.listen` only when `require.main === module` so tests can import the app.

### Other stacks
Apply the same layer table with the framework's idioms (Go: `internal/{config,handlers,services,repositories}`;
Rails/Laravel already ship MVC — use Fix-only mode; Java Spring: `controller/service/repository/model`).

## 4. Adaptive modes

| Mode | When | Do | Keep |
|---|---|---|---|
| **Monolith decomposition** | Phase 1 = Monolith | create every layer; move each function of the flat modules into its layer; delete the flat modules (`models.py`, `controllers.py`, `AppManager.js`, `utils.js`) in the same step | entry point path, run command, endpoint contract |
| **Partial-layering gap-fill** | Phase 1 = Partial layering | keep existing `models/`, `routes/`, `services/`, `utils/` and their names; add `config/`, `controllers/`, `middlewares/`, `validators/`, `errors.py`; move business logic + validation + serialization out of routes into controllers/services/validators/models; split misnamed route modules (`report_routes.py` → `report_routes.py` + `category_routes.py`); fix dead services instead of deleting them if they represent a real concern (make them config-driven); delete helpers with zero references after the move | existing packages, `seed.py` import path (`from app import app, db` must still work), blueprint names |
| **Fix-only** | Phase 1 = MVC-compliant | apply security/quality patterns (P1, P2, P4, P5, P6, P9, P11–P15) without moving files | everything |

Rule: never leave a flat module next to a same-named package (`models.py` + `models/`).
After moving code, `grep -rn "import models\|import controllers\|from database import get_db\|require('./AppManager')\|require('./utils')"` must return nothing stale.

## 5. Behavioural contract (the "do not break" list)

Preserve:
1. Entry point path and run command (`python app.py`, `npm start`, `python seed.py`).
2. Every `METHOD + PATH` from the Phase 1 inventory (including `/`, `/health`, admin routes).
3. Success status codes and **top-level JSON keys** (`dados`, `sucesso`, `mensagem`, `msg`,
   `enrollment_id`, `overdue`, `task_count`, …) and array shapes.
4. Error status codes, messages and envelope key (`{"erro": ...}` / `{"error": ...}` / plain text).
5. Seed scripts and seeded credentials (login with seeded users must still succeed on a fresh DB
   **and** on a pre-existing DB file with legacy hashes/plaintext → verify-and-upgrade).
6. Query parameters, path converters, default values.

Allowed deviations (must be listed under `## Contract changes (security-driven)`):
- removing leaked sensitive fields (`senha`, `password`, `secret_key`, `debug`, `db_path`);
- privileged/destructive endpoints require `X-Admin-Token` (401 wrong token, 403 when
  `ADMIN_TOKEN` unset) — they still exist and respond;
- raw-SQL endpoints restricted to read-only `SELECT`;
- responses that previously returned 500 for client mistakes now return 400/404;
- delete endpoints that now also remove dependants (message text may change, status kept).

## 6. Config module rules

- Every value has a default so the app boots with **no `.env`** and no exported variables.
- Secrets default to obviously-dev values (`dev-only-change-me`) and log a warning when the default is used.
- Standard names: `SECRET_KEY`, `DEBUG` (`"true"/"false"`), `HOST` (default `0.0.0.0` only if the
  original did; prefer `127.0.0.1` for dev), `PORT` (original port), `DATABASE_URL` / `DB_PATH`
  (original file), `ADMIN_TOKEN` (default unset), `CORS_ORIGINS` (`*` to keep behaviour, documented),
  `LOG_LEVEL`, `SMTP_*`, `PAYMENT_GATEWAY_KEY`.
- Ship `.env.example` with every key and a comment; never commit `.env`.
- Python: `config/settings.py` using `os.getenv`, optional `python-dotenv` only if already a dependency.
- Node: `config/index.js` reading `process.env`, `Object.freeze`, numeric parsing for `PORT`.

## 7. Error handling contract

- Flask: `errors.py` with `AppError(status, message)`, `NotFoundError`, `ValidationError`,
  `UnauthorizedError`, `ForbiddenError`; `middlewares/error_handler.py::register_error_handlers(app)`
  handling `AppError` → `(status, {<envelope>: message})`, `HTTPException` → its code with the same
  envelope, `Exception` → log + generic 500 (never `str(e)` to the client). Remove per-handler
  `try/except` blocks that only re-encode errors.
- Express: `errors/AppError.js`; `middlewares/errorHandler.js` `(err, req, res, next)` mapping
  `AppError` → status + message (plain text when the project used text errors, JSON otherwise),
  JSON parse errors → 400, unknown → log + 500; `middlewares/notFound.js`; `asyncHandler(fn)`.

## 8. Security baseline for Phase 3 output

- [ ] no secrets or environment literals in source (`grep` for the old literals returns nothing)
- [ ] every SQL statement parameterised
- [ ] passwords hashed with a KDF; legacy verify-and-upgrade in place
- [ ] no password/hash/secret in any response; no card numbers/keys/PII in logs
- [ ] privileged endpoints guarded; raw SQL read-only
- [ ] `DEBUG` defaults to false; CORS policy from env
- [ ] centralized error handler; no `str(e)` leaks
- [ ] deprecated APIs replaced per catalog AP-14
