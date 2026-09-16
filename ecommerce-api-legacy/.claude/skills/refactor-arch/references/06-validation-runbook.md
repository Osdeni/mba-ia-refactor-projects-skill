# 06 — Validation Runbook (Phase 3)

Validation proves two things: the refactored app **boots** and **every original endpoint still
responds** with the same status and shape. Run the baseline against the ORIGINAL code before
editing, and the same list against the refactored code after.

## 1. Toolchain setup

**Python** (always an isolated venv inside the project; it is gitignored):
```bash
[ -x .venv/bin/python ] || python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt          # timeout 300s
PY=.venv/bin/python
```
Always call `$PY` explicitly (never bare `python`).

**Node**:
```bash
[ -d node_modules ] || npm install --no-audit --no-fund   # timeout 600s (sqlite3 may compile natively)
```
If `npm install` fails on a native module, retry once with `npm install --build-from-source` only
if `g++`, `make` and `python3` exist; otherwise stop and report the missing prerequisite.

## 2. Port selection

```bash
DEFAULT=<port from Phase 1>
PORT=$DEFAULT; while ss -ltn 2>/dev/null | grep -q ":$PORT "; do PORT=$((PORT+1)); done; echo $PORT
```
Baseline of the ORIGINAL app: the port is hardcoded, so if `DEFAULT` is busy start the original
with an override when possible (Flask: `python -c "from app import app; app.run(host='127.0.0.1', port=$PORT, use_reloader=False)"`);
for Node with a literal `app.listen(3000)` and port busy, skip the baseline and use the documented
expectations (`api.http`, README) as the reference. After the refactor, always pass `PORT=$PORT`.

## 3. Boot in background (mandatory recipe)

```bash
NAME=$(basename "$PWD"); LOG=/tmp/refactor-arch-$NAME.log; PIDF=/tmp/refactor-arch-$NAME.pid
# Flask (original, no reloader)
nohup $PY -c "from app import app; app.run(host='127.0.0.1', port=$PORT, use_reloader=False)" > $LOG 2>&1 & echo $! > $PIDF
# Flask (refactored)
DEBUG=false HOST=127.0.0.1 PORT=$PORT ADMIN_TOKEN=validation-token nohup $PY app.py > $LOG 2>&1 & echo $! > $PIDF
# Node
PORT=$PORT ADMIN_TOKEN=validation-token nohup node src/app.js > $LOG 2>&1 & echo $! > $PIDF
# readiness (max 20s)
for i in $(seq 1 20); do curl -s -o /dev/null http://127.0.0.1:$PORT/<first GET route> && break; sleep 1; done
```
Never start a server in the foreground (the tool call would hang). Never use the Flask reloader
during validation (it forks a child that survives `kill`).

Teardown (always, even on failure):
```bash
kill $(cat $PIDF) 2>/dev/null; sleep 1; pkill -f "app.py|src/app.js" 2>/dev/null
ss -ltn | grep -q ":$PORT " && echo "PORT STILL BUSY" ; rm -f $PIDF
```
Keep the log until the completion block is printed (quote its tail on failures).

## 4. Smoke-test list (derived from the Phase 1 route inventory)

Order: read-only GETs → `POST` creates (capture created ids) → `PUT`/`DELETE` on the created ids
→ reports → privileged/destructive admin routes **last** (`reset-db`, `DELETE /users/:id`).
Never delete seeded records that later calls depend on before those calls run.

Bodies: infer required fields from the validators / original handlers / `api.http` / README.
Always send `-H 'Content-Type: application/json'` for JSON bodies. For guarded routes send
`-H 'X-Admin-Token: validation-token'`.

Helper:
```bash
call() { # METHOD PATH [JSON] [extra curl args...]
  local m=$1 p=$2 d=${3:-}; shift 3 2>/dev/null || shift $#
  if [ -n "$d" ]; then
    curl -s -o /tmp/ra-body -w '%{http_code}' -X "$m" "http://127.0.0.1:$PORT$p" -H 'Content-Type: application/json' -d "$d" "$@"
  else
    curl -s -o /tmp/ra-body -w '%{http_code}' -X "$m" "http://127.0.0.1:$PORT$p" "$@"
  fi
  echo " $m $p -> keys: $(python3 -c "import json,sys;b=open('/tmp/ra-body').read()
try:
  j=json.loads(b); print(sorted(j.keys()) if isinstance(j,dict) else 'array[%d]'%len(j))
except Exception: print('text:'+b[:40].replace(chr(10),' '))")"
}
```
Record, per route: `status`, `keys` (top-level keys for objects, `array[n]` for arrays, `text:`
prefix for plain text).

## 5. Baseline vs after — comparison rules

A route passes when `status` is equal and the `keys`/shape are equal, **except** for the allowed
deviations listed in guidelines §5 (removed sensitive fields; 401/403 on guarded routes without
the header — in that case call again with the header and compare that; 400 where the original
returned 500 for invalid input). Any other difference is a failure to fix.

Also run the failure probes that used to crash: empty body on a POST/PUT, wrong types
(`"preco": "abc"`, `"priority": "2"`, numeric `card`), non-existent ids — the refactored app must
answer 400/404, never 500, and must stay alive afterwards.

## 6. Re-audit pass ("zero anti-patterns remaining")

Re-run the catalog quick grep sheet on the refactored tree (excluding `.venv`, `node_modules`,
`.claude`). Expected: no CRITICAL/HIGH signals (no literal secrets, no string-built SQL, no
`str(e)` leaks, no `debug=True` literal, no `md5`/`badCrypto`, no `utcnow`, no `Model.query.get`).
Remaining LOW items must be listed explicitly in the completion block.

Static checks: Python `$PY -m py_compile $(git ls-files '*.py')` (or `find`-based);
Node `node --check src/**/*.js` (loop over files).

## 7. Completion block format

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<`find . -type f -not -path './.venv/*' -not -path './node_modules/*' -not -path './.claude/*' -not -path './.git/*' -not -path '*/__pycache__/*' -not -path './reports/*' | sort` rendered as a tree>

## Validation
  ✓ Application boots without errors (port <PORT>, <seconds>s)
  ✓ All endpoints respond correctly (<ok>/<total> — see table)
  ✓ Zero CRITICAL/HIGH anti-patterns remaining (<n> LOW accepted: <list>)

## Endpoint check
| METHOD | PATH | baseline | after | keys match |
| GET | /produtos | 200 [dados,sucesso] | 200 [dados,sucesso] | yes |

## Contract changes (security-driven)
- GET /health: removed secret_key, debug, db_path
- POST /admin/query: requires X-Admin-Token; SELECT only

## Next steps
- Review the diff and commit the refactored code
- Report kept at <report path>
================================
```
Use `✗` and add `## Failed checks` (with the log tail and what was tried) if anything remains
broken after 3 fix loops. Never claim success for a check that was not executed.

## 8. Fix loop

On a failed boot or route: `tail -50 $LOG` → identify the stale import / missing module / wrong
env name → fix → teardown → boot again → re-run the whole list (not just the failed route).
Maximum 3 loops; after that, report honestly.
