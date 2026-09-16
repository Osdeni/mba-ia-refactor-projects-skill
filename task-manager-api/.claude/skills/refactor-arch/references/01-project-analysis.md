# 01 — Project Analysis Heuristics (Phase 1)

Goal: in a few commands, determine language, framework, database, entry point, route inventory,
architecture classification and domain. Everything here is evidence-based: cite the file that
proved each fact.

## 1. Scope rules — what counts as a "source file"

Include files with the primary language extension found under the project root.
Exclude: `.claude/`, `.git/`, `reports/`, `.venv/`, `venv/`, `node_modules/`, `__pycache__/`,
`instance/`, `dist/`, `build/`, lockfiles (`package-lock.json`, `poetry.lock`), `*.db`, `*.sqlite`,
`*.log`, `*.md`, `*.http`, `*.txt`, `*.json` (unless it is the only source form).

```bash
# file inventory (adjust extensions after language detection)
find . -type f \( -name '*.py' -o -name '*.js' -o -name '*.ts' -o -name '*.go' -o -name '*.rb' -o -name '*.php' -o -name '*.java' -o -name '*.cs' \) \
  -not -path './.claude/*' -not -path './.git/*' -not -path './node_modules/*' -not -path './.venv/*' \
  -not -path './venv/*' -not -path '*/__pycache__/*' -not -path './instance/*' -not -path './reports/*' | sort
# lines of code
<same find> | xargs wc -l | tail -1
```

`Source files: N` = number of files in that list. `~LOC` = the wc total.

## 2. Language detection

| Marker | Language |
|---|---|
| `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py`, `*.py` | Python |
| `package.json` (+ `tsconfig.json` → TypeScript) | JavaScript / TypeScript (Node.js) |
| `go.mod` | Go |
| `pom.xml`, `build.gradle` | Java / Kotlin |
| `Gemfile` | Ruby |
| `composer.json` | PHP |
| `*.csproj` | C# |

If several markers exist, the language with the most source files wins; mention the others.

## 3. Framework and version

**Python**
- Pinned version: `grep -iE '^(flask|django|fastapi|bottle|tornado)' requirements.txt` → `flask==3.1.1`.
- Code signals: `from flask import`, `Flask(__name__)`, `Blueprint(`, `flask_sqlalchemy`, `FastAPI(`, `django`.
- If not pinned: `.venv/bin/pip show flask 2>/dev/null | grep Version` or `pip show`.

**Node.js**
- Declared range: `package.json` → `"express": "^4.18.2"`.
- Resolved version (works without `node_modules`): `grep -A2 '"node_modules/express"' package-lock.json | grep version`.
- Code signals: `require('express')`, `express()`, `app.listen(`, `express.Router()`, `fastify(`, `new Koa()`, `@nestjs`.

Report as `Framework: Express 4.22.1 (declared ^4.18.2)` when both are known, else the declared one.

**Dependencies:** runtime deps only (not dev), comma-separated, excluding the framework itself.
Note deps declared but never imported (dead dependencies) — that is a finding for Phase 2.

## 4. Database detection

| Signal | Conclusion |
|---|---|
| `import sqlite3`, `sqlite3.connect(` | SQLite via stdlib (file path in the call) |
| `require('sqlite3')`, `new sqlite3.Database(':memory:')` | SQLite (in-memory if `:memory:`) |
| `SQLALCHEMY_DATABASE_URI`, `db.Model`, `flask_sqlalchemy` | SQLAlchemy ORM (dialect from the URI) |
| `psycopg2`, `pg`, `mysql2`, `pymysql`, `mongoose`, `pymongo` | Postgres / MySQL / MongoDB |
| `sequelize`, `prisma`, `typeorm`, `knex` | Node ORM / query builder |

Tables: from `CREATE TABLE` statements (`grep -n 'CREATE TABLE'`), `__tablename__`, classes
inheriting `db.Model`/`Base`, migration folders. Record: file-based vs in-memory, whether the DB
file is gitignored (`cat .gitignore`), whether seeds run at boot.

## 5. Entry point, run command, port

- Python: `if __name__ == "__main__"`, `app.run(host=..., port=..., debug=...)`, `flask --app`,
  `gunicorn` in a Procfile/Dockerfile. Note `debug=True` and host `0.0.0.0` literals (security signal).
- Node: `package.json` → `"main"`, `"scripts"."start"`; `app.listen(<port>)`; port literal or `process.env.PORT`.
- Record the exact run command a developer uses today (`python app.py`, `npm start`) — Phase 3 must keep it working.

## 6. Route inventory (mandatory — this is the Phase 3 contract)

```bash
# Flask
grep -nE "add_url_rule\(|@(app|[a-z_]+_bp|[a-z_]+)\.route\(|register_blueprint\(" -r . --include='*.py' | grep -v '.venv'
# Express
grep -nE "\b(app|router)\.(get|post|put|patch|delete|use|all)\(" -r src --include='*.js' --include='*.ts'
```

Produce a table:

| METHOD | PATH | handler (file:line) | success (status + top-level keys) | error envelope |
|---|---|---|---|---|
| GET | /produtos | controllers.py:5 | 200 `{dados: [...]}` | `{erro}` |

Rules: include routes defined inline in the entry point; resolve blueprint `url_prefix`; note the
error envelope key (`erro`, `error`, `message`, or plain text) — the refactor must reuse it.
Count = `Endpoints: N routes`.

## 7. Architecture classification (drives the Phase 3 mode)

Check for the layer directories/modules: `models`, `routes|views|blueprints`, `controllers|handlers`,
`services`, `config|settings`, `middlewares`, `repositories`.

| Classification | Criteria | Phase 3 mode |
|---|---|---|
| **Monolith** | 0–1 layers present; a single file/class owns DB setup + queries + routing + business rules; flat files at the root (`app.py`, `models.py`, `controllers.py`, `AppManager.js`) | Monolith decomposition |
| **Partial layering** | 2–3 layers present (e.g. `models/` + `routes/` + `services/`) but no `config`, no `controllers`, no `middlewares`, and/or routes contain business logic, validation, ORM calls and serialization | Partial-layering gap-fill |
| **MVC-compliant** | models, controllers, routes/views, config and centralized error handling exist and routes are thin | Fix-only (security/quality findings) |

Write the classification as `<Class> — <one-line justification>`, e.g.
`Monolítica — tudo em 4 arquivos, sem separação de camadas` or
`Parcialmente organizada — models/routes/services existem, mas as rotas concentram regra de negócio e SQL`.

## 8. Domain inference

Combine: table/entity names, README title, `package.json.description`, route prefixes, log
messages. Output one line with the main entities in parentheses, in the project's language:
`E-commerce API (produtos, pedidos, usuários)`, `LMS API com checkout (users, courses, enrollments, payments)`,
`Task Manager API (tasks, users, categories)`.

## 9. Output

Print the `PHASE 1: PROJECT ANALYSIS` block exactly as defined in SKILL.md. Keep the route
inventory and the file list in context for Phases 2 and 3.
