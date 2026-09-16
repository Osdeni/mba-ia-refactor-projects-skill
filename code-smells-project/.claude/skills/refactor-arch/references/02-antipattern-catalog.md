# 02 — Anti-pattern Catalog (Phase 2)

## Severity scale

- **CRITICAL** — security or architecture flaws that prevent correct operation, expose sensitive
  data (hardcoded credentials, SQL injection, plaintext passwords, secrets in responses/logs) or
  completely violate separation of concerns (a "God Class" holding database, business logic and
  routing in one file).
- **HIGH** — strong MVC/SOLID violations that make maintenance and testing very hard (heavy
  business logic inside controllers/routes, tight coupling with no dependency injection, global
  mutable state, no centralized error handling, insecure runtime defaults).
- **MEDIUM** — standardisation, duplication or moderate performance problems (N+1 queries,
  misuse/absence of middlewares, missing validation, deprecated API usage, integrity gaps).
- **LOW** — readability: naming, magic numbers, dead code, print-logging, deep nesting.

## Detection method

1. Always use `grep -nE` (or `rg -n`) so every finding carries an exact line.
2. Confirm each hit by reading the surrounding lines; do not report from grep alone.
3. One finding per (file, anti-pattern) cluster; list secondary lines in the description.
4. An entry may yield several findings across files; a file may match several entries.
5. Severity may move one level with a one-line justification (e.g. a "MEDIUM validation gap" that
   assigns a default password becomes HIGH).
6. Minimums for a legacy project: ≥5 findings, ≥1 CRITICAL/HIGH. If below, re-run the grep sheet
   (§ Quick grep sheet) before concluding.

## Catalog

Format: **ID · Name · Severity** — why it matters · detection signals per stack · recommendation (playbook pattern).

### AP-01 · Hardcoded credentials & configuration · CRITICAL
Secrets and environment-specific values baked into source are leaked through git history and
cannot vary per environment.
- Python/Flask: `SECRET_KEY = '...'`, `app.config["SECRET_KEY"] = "<literal>"`, `password =`,
  `smtp`, `api_key`, `token` string literals; `sqlite:///...` or DB path literals in config;
  `app.run(host=..., port=...)` literals; `os.environ`/`os.getenv` never referenced.
- Node/Express: object literals with `dbPass`, `apiKey`, `paymentGatewayKey`, `smtpUser`,
  `port: 3000`; `process.env` never referenced; no `.env.example`.
- Recommendation: env-backed config module with safe defaults + `.env.example` (**P1**).

### AP-02 · SQL injection (string-built queries) · CRITICAL
User input interpolated into SQL allows auth bypass, data theft and destruction; apostrophes
break the query.
- Python: `execute("..." + var)`, f-strings/`%`/`.format()` inside `execute(`, `"LIKE '%" +`,
  `WHERE ... = '" + `; no `?`/`%s` placeholders; raw client SQL executed (`execute(dados["sql"])`).
- Node: template literals or `+` inside `db.run/get/all/query(`, missing params array;
  `knex.raw`/`sequelize.query` with interpolation.
- Recommendation: parameterised queries; dynamic filters built as clause + param lists; whitelist
  for identifiers (**P2**).

### AP-03 · God class / God module · CRITICAL
One file or class owns DB setup, queries, validation, business rules, routing and formatting for
several domains: untestable, every change touches everything.
- Python: module > ~250 LOC serving ≥3 domains; `app.py` defining routes with cursor/SQL inline;
  `models.py` containing validation + SQL + dict formatting for all entities; no packages.
- Node: a class with `new sqlite3.Database` + `initDb()` + `setupRoutes(app)` + payment rules;
  route closures > 40 lines; `src/` with 1–3 files.
- Recommendation: decompose by domain into config/models/services/controllers/routes (**P3**).

### AP-04 · Weak or plaintext credential storage · CRITICAL
Plaintext or reversible/unsalted "hashes" turn any DB read into a credential dump.
- Python: `senha`/`password` stored as received; `WHERE senha = `; `hashlib.md5`/`sha1` for
  passwords; seeds with plaintext passwords; no `werkzeug.security`/`bcrypt`/`argon2`.
- Node: custom hash functions (`badCrypto`), `Buffer.from(pwd).toString('base64')`, `md5`,
  seeds like `pass '123'`; no `bcrypt`/`scrypt`/`argon2`.
- Recommendation: KDF hashing with legacy verify-and-upgrade so seeded users keep working (**P4**).

### AP-05 · Sensitive data exposure (responses & logs) · CRITICAL
Secrets, password hashes, card numbers or PII returned by the API or written to logs.
- Python: `to_dict()` returning `password`; `SELECT *` mapped to dicts including `senha`;
  `/health` or `/` returning `secret_key`, `debug`, `db_path`; `print(email)`/tokens.
- Node: `console.log` of card numbers/keys/tokens; `res.json(user)` including `pass`; error
  responses with stack traces.
- Recommendation: whitelist serializers, log redaction/masking (**P5**).

### AP-06 · Unprotected privileged or dangerous endpoints · CRITICAL
Admin, destructive or raw-SQL endpoints reachable without authentication/authorization.
- Python: routes executing client SQL; `DELETE FROM` all tables via HTTP; `/admin/*` without an
  auth decorator; login returning the user without issuing any token; no `before_request` guard.
- Node: `/api/admin/*` or `app.delete` routes with no auth middleware; destructive routes returning
  200 unconditionally; `'fake-jwt-token-' + id`.
- Recommendation: admin-token guard from env (+ read-only restriction for raw SQL) (**P6**).

### AP-07 · Business logic in route handlers (fat controllers) · HIGH
Handlers that parse, validate, compute prices/rules, persist, notify and format in one function
cannot be unit-tested or reused.
- Python: handler > 30 lines; validation chains, price/discount math, notification `print`s,
  transactions or `db.session.commit()` inside route functions; blueprints importing `db` and
  mutating models directly; 90-line report endpoints.
- Node: route closure containing DB calls, payment decision (`cc.startsWith("4")`), persistence
  and cache writes; nested callbacks inside the handler.
- Recommendation: thin controller + service extraction (**P7**).

### AP-08 · Global mutable state / shared connection · HIGH
Module-level mutable singletons shared across requests are race-prone and untestable.
- Python: `db_connection = None` + `global`; `sqlite3.connect(..., check_same_thread=False)`;
  module-level `app` with `db.create_all()` at import; in-memory lists on singleton services.
- Node: module-level `let globalCache = {}`, `let totalRevenue = 0`; exported mutable primitives;
  DB created inside a constructor with no injection.
- Recommendation: request-scoped DB access (`flask.g` + teardown), app factory, injected
  services (**P8**).

### AP-09 · No centralized error handling / exception swallowing · HIGH
Identical try/except blocks in every handler leak internals, hide root causes and return wrong
status codes; uncaught errors crash Node processes.
- Python: `except Exception as e: return jsonify({"erro": str(e)}), 500` repeated; bare `except:`;
  no `@app.errorhandler`; `HTTPException` (400/404/415) converted into 500.
- Node: no 4-arg `(err, req, res, next)` middleware; no 404 handler; callbacks ignoring `err`;
  repeated `if (err) return res.status(500).send("Erro DB")`; no `unhandledRejection` handler.
- Recommendation: error classes + one error handler + 404 handler (**P9**).

### AP-10 · Insecure runtime defaults · HIGH
Debug servers, open CORS and all-interfaces binding hardcoded into the entry point.
- Python: `debug=True`, `app.config["DEBUG"] = True`, `host="0.0.0.0"` literal, `CORS(app)` with
  no origins; `app.run` as the only deployment path.
- Node: no `NODE_ENV` handling; port literal; stack traces sent to clients; no `helmet`/CORS policy.
- Recommendation: env-driven `DEBUG`, `HOST`, `PORT`, `CORS_ORIGINS` (**P1**).

### AP-11 · Callback hell / tight coupling without dependency injection · HIGH
Deeply nested callbacks and hard-wired construction hide control flow and forbid substitution.
- Python: controllers importing `get_db` directly; functions creating their own connections;
  nesting > 4 levels.
- Node: ≥3 nested callbacks in one handler; `const self = this`; manual completion counters
  (`pending--`); `new Database()` inside constructors; `setupRoutes(app)` mutating the app.
- Recommendation: promisified data layer + async/await; constructor/module injection (**P10**).

### AP-12 · N+1 queries · MEDIUM
A query inside a loop over a previous result multiplies round-trips.
- Python: `cursor.execute` inside `for row in rows`; `Model.query.get(x.fk)` inside loops;
  `len(u.tasks)` per user; `filter_by(user_id=u.id)` per user; 5 separate `COUNT` queries that a
  `GROUP BY` would replace.
- Node: `db.get/all` inside `forEach` over a previous result set.
- Recommendation: JOIN / eager load / aggregate query (**P11**).

### AP-13 · Duplicated logic (validation, serialization, rules) · MEDIUM
Copy-pasted blocks drift and become bugs.
- Python: same row→dict block repeated; same required-field checks in create/update (already
  divergent); business rule (`overdue`) computed inline in ≥3 places while a model method exists;
  status whitelists repeated.
- Node: repeated `res.status(500).send(...)` blocks; repeated field checks; duplicated queries.
- Recommendation: validators + serializers as single sources of truth (**P12**).

### AP-14 · Deprecated / legacy API usage · MEDIUM
Obsolete APIs emit warnings today and break on the next upgrade; modern equivalents exist.

| Stack | Deprecated / legacy usage | Modern equivalent |
|---|---|---|
| Python ≥3.12 | `datetime.utcnow()`, `datetime.utcfromtimestamp()` | `datetime.now(timezone.utc)` (store naive UTC via `.replace(tzinfo=None)` if the schema needs it) |
| Python 3.12 sqlite3 | implicit transaction control via `isolation_level` | explicit `with conn:` blocks / `conn.autocommit` |
| Python | `hashlib.md5/sha1` for passwords | `werkzeug.security.generate_password_hash` / `bcrypt` / `argon2` |
| Flask ≥2.3 | `@app.before_first_request` (removed), `flask.json.JSONEncoder` (removed), `werkzeug.security.safe_str_cmp` (removed) | `with app.app_context()` at factory time, `app.json` provider, `hmac.compare_digest` |
| Flask ≥2.1 | `request.get_json()` assumed to return `None` on wrong content type | it raises 415 — use `get_json(silent=True)` and validate |
| Flask | `app.run(debug=True)` as production server | `flask run` for dev, gunicorn/waitress for prod |
| SQLAlchemy 2.x | `Model.query.get(id)`, `Model.query.filter_by(...)` (legacy Query API, `LegacyAPIWarning`) | `db.session.get(Model, id)`, `db.session.execute(select(Model)...)` / `db.session.scalars(...)` |
| Flask-SQLAlchemy 3 | `SQLALCHEMY_TRACK_MODIFICATIONS = False` (now default) | remove |
| Node | callback-style `sqlite3` API | promisified wrapper, `node:sqlite` (Node ≥22.5) or `better-sqlite3` |
| Node | `new Buffer()`, `Buffer()` | `Buffer.from` / `Buffer.alloc` |
| Node | `util.isArray`, `util._extend`, `url.parse()`, `crypto.createCipher`, `require('sys')`, `domain` | `Array.isArray`, `Object.assign`, `new URL()`, `createCipheriv`, `util`, async error handling |
| Express | `bodyParser.json()`, `app.del()`, `req.param()`, `res.send(status)`, `res.sendfile()`, `res.json(status, obj)`, `app.configure()` | `express.json()`, `app.delete()`, `req.params/query/body`, `res.sendStatus()`, `res.sendFile()`, `res.status().json()` |
| Express 4 | maintenance-only major; async errors not propagated | Express 5 (async handlers propagate errors) or `asyncHandler` wrapper on 4 |
| JS | `substr()`, `var`, `arguments.callee` | `slice()`, `const`/`let`, named functions |
| CORS | `flask-cors < 6` (private-network header advisory) | `flask-cors >= 6` |

- Detection: grep the left column; also check pinned versions against current majors.
- Recommendation: modernization table applied file by file (**P13**).

### AP-15 · Missing or inconsistent input validation · MEDIUM
Unvalidated input reaches SQL/business logic and produces 500s or corrupt data.
- Python: `request.get_json()` used without `if not data`; `int(request.args[...])` unguarded;
  comparisons without type checks (`priority < 1` on a string → TypeError); negative quantities
  accepted; regex that accepts `a@b`.
- Node: body fields read without validation; no schema; required field (`pwd`) missing from the
  check; numeric fields not coerced (`card` as number crashes `startsWith`).
- Recommendation: validators returning 400 with the project's existing messages (**P12**).

### AP-16 · Data integrity gaps (no FK / cascade / transactions) · MEDIUM
Orphans, partial writes and inconsistent totals.
- Python: `CREATE TABLE` without `FOREIGN KEY`/`NOT NULL`/`UNIQUE`; multi-step writes with
  commit only at the end but early returns; manual delete loops instead of cascade; delete leaving
  dangling `category_id`; `PRAGMA foreign_keys` never enabled.
- Node: `DELETE FROM users` leaving enrollments/payments; multi-insert checkout without
  `BEGIN/COMMIT`; `REAL` money columns.
- Recommendation: FK + cascade + transaction wrapper (**P14**).

### AP-17 · Magic numbers / strings · LOW
Unexplained literals encode business rules.
- Python: discount thresholds (`10000/5000/1000`, `0.1/0.05/0.02`), status lists inline,
  `len(password) < 4`, `timedelta(days=7)`, `'#000000'`, version strings duplicated.
- Node: `cc.startsWith("4")`, `"123456"` default password, `10000` loop, `'PAID'`/`'DENIED'` literals.
- Recommendation: constants/enums module (**P15**).

### AP-18 · Cryptic or inconsistent naming · LOW
Names that hide intent or mislead.
- Python: `t, u, c, p1..p5, td`; parameter `id` shadowing the builtin; mixed pt/en identifiers;
  module names that do not match content (`report_routes.py` hosting category CRUD).
- Node: `usr, eml, pwd, c_id, cc`; `e` meaning e-mail; `AppManager`; `utils.js` junk drawer.
- Recommendation: rename internally, keep external field names (**P15**).

### AP-19 · Code hygiene: print-logging, dead code, unused imports, deep nesting · LOW
- Python: `print(` as logging; unused imports (`os, sys, json, time, hashlib`); unused modules
  (`services/`, helper functions never called); `if cond: return True else: return False`;
  4-level nested `if/else`; dependencies declared but never imported.
- Node: `console.log` everywhere; unused exports (`totalRevenue`); `let` for constants; no linter.
- Recommendation: logger, delete dead code, guard clauses (**P15**).

## Quick grep sheet

Run the block for the detected stack; every hit is a candidate finding to confirm by reading.

```bash
# ---------- Python / Flask ----------
grep -rnE "SECRET_KEY\s*=|password\s*=\s*['\"]|senha\s*=\s*['\"]|api_key|smtp_|sqlite:///|debug=True|DEBUG\"?\]?\s*=\s*True|host=['\"]0\.0\.0\.0" --include='*.py' . | grep -v .venv
grep -rnE "execute\((f['\"]|['\"][^'\"]*['\"]\s*\+|.*%\s*\(|.*\.format\()" --include='*.py' . | grep -v .venv
grep -rnE "\" \+ str\(|' \+ [a-z_]+ \+ '|LIKE '%\" \+" --include='*.py' . | grep -v .venv
grep -rnE "hashlib\.(md5|sha1)|\"senha\": row|'password': self\.password|secret_key|fake-jwt" --include='*.py' . | grep -v .venv
grep -rnE "check_same_thread=False|^db_connection|global db|create_all\(\)" --include='*.py' . | grep -v .venv
grep -rnE "except:|except Exception as e:\s*$|str\(e\)" --include='*.py' . | grep -v .venv
grep -rnE "\.query\.get\(|\.query\.|utcnow\(|before_first_request|JSONEncoder|safe_str_cmp|TRACK_MODIFICATIONS" --include='*.py' . | grep -v .venv
grep -rnE "^\s*for .* in .*:$" -A4 --include='*.py' . | grep -E "execute\(|\.query\.|len\([a-z]+\.[a-z]+\)" | grep -v .venv
grep -rnE "^\s*print\(" --include='*.py' . | grep -v .venv
grep -rnE "^import .*,|^from .* import .*,.*,.*,"  --include='*.py' . | grep -v .venv
grep -rnE "type\(.*\) == |== True|== False|if .*:\s*$" --include='*.py' . | grep -v .venv | head -40
grep -rnE "CORS\(app\)$|CORS\(app, *\)" --include='*.py' . | grep -v .venv
grep -rnE "get_json\(\)" --include='*.py' . | grep -v .venv
grep -rnE "add_url_rule|@app\.route|\.route\(" --include='*.py' . | grep -v .venv | wc -l

# ---------- Node / Express ----------
grep -rnE "pass(word)?\s*:\s*['\"]|Key\s*:\s*['\"]|secret|smtp|port\s*:\s*[0-9]+|process\.env" src
grep -rnE "console\.log\(.*(card|cart|pass|token|key|secret)" src
grep -rnE "db\.(run|get|all|exec)\((\`|['\"][^'\"]*['\"]\s*\+)" src
grep -rnE "base64|md5|sha1|createHash|badCrypto|bcrypt|scrypt|argon" src
grep -rnE "^\s*(let|var) [a-zA-Z_]+ = (\{\}|\[\]|0);|module\.exports" src
grep -rnE "app\.(get|post|put|delete|use)\(|router\." src
grep -rnE "\(err, [a-z]+\) =>|function\(err\)|function \(err\)" src | wc -l
grep -rnE "\(err, req, res, next\)|unhandledRejection|uncaughtException" src
grep -rnE "forEach\(|for \(" -A3 src | grep -E "db\.(get|all|run)"
grep -rnE "new Buffer\(|bodyParser|util\.isArray|url\.parse|createCipher\(|\.substr\(|req\.param\(|res\.sendfile|app\.del\(" src
grep -rnE "startsWith\(\"[0-9]\"\)|\"123456\"|10000" src
grep -rnE "^\s*(let|const) [a-z]{1,3} = req\.body" src
grep -nE "\"(express|sqlite3|body-parser)\"" package.json
```
