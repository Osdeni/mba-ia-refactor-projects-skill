---
name: refactor-arch
description: Analyze, audit and refactor any backend project to the MVC pattern in 3 sequential phases — (1) stack/architecture analysis, (2) anti-pattern audit with a severity-ranked report and a mandatory confirmation gate, (3) MVC refactoring validated by booting the app and hitting every endpoint. Technology-agnostic (Python/Flask, Node/Express and others). Use when asked to refactor architecture, audit code smells, or migrate a legacy API to MVC.
argument-hint: "[optional path where the audit report will be saved]"
---

# refactor-arch — Architecture Audit & MVC Refactoring

You are a senior software architect running a 3-phase pipeline on the project in the
**current working directory**. Knowledge lives in the reference files below; read each one
at the step that names it (paths are relative to the project root):

| File | Read at |
|---|---|
| `.claude/skills/refactor-arch/references/01-project-analysis.md` | Phase 1 |
| `.claude/skills/refactor-arch/references/02-antipattern-catalog.md` | Phase 2 |
| `.claude/skills/refactor-arch/references/03-audit-report-template.md` | Phase 2 |
| `.claude/skills/refactor-arch/references/04-mvc-guidelines.md` | Phase 3 |
| `.claude/skills/refactor-arch/references/05-refactoring-playbook.md` | Phase 3 |
| `.claude/skills/refactor-arch/references/06-validation-runbook.md` | Phase 3 |

## Ground rules (apply to every phase)

1. **Scope:** operate only inside the current working directory (the project root). Never edit
   anything under `.claude/`. The only file written before Phase 3 is the audit report.
2. **Sequential phases.** Phase 3 NEVER starts in the same turn as Phase 2. The Phase 2 gate is
   implemented by *ending your turn* right after the confirmation question.
3. **No clarifying questions** in Phases 1–2: infer from the code. Do not use interactive tools
   (no AskUserQuestion). The only pause is the Phase 2 gate.
4. **Headless-friendly output.** The run may be non-interactive (`claude -p`), where only the final
   message of each turn is shown. Therefore the final message of turn 1 must contain the Phase 1
   block + the full audit report + the gate line; the final message of turn 2 must contain the
   validation results + the completion block.
5. **Servers:** always start them in the background with a log file and a PID file, poll for
   readiness, and always kill them before the turn ends (see runbook).
6. **Language:** fixed labels/headers exactly as in the templates (English); free-text prose in the
   language of the project's README (Portuguese for pt-BR projects).
7. **Report path:** if `$ARGUMENTS` is non-empty, it is the output path for the audit report
   (relative to the project root, may point outside it, e.g. `../reports/audit-project-1.md`);
   otherwise use `reports/audit-<project-dir-name>.md`. Create parent directories as needed.

Arguments received: `$ARGUMENTS`

---

## PHASE 1 — PROJECT ANALYSIS

1. Read `references/01-project-analysis.md`.
2. Inventory the source files (apply the exclusion list), detect **language, framework + version,
   dependencies, database + tables, entry point + run command + port**, build the **route
   inventory table** (METHOD | PATH | handler `file:line` | success shape | error envelope) and
   keep it — it is the behavioural contract for Phase 3.
3. Classify the architecture (`Monolith` / `Partial layering` / `MVC-compliant`) and infer the
   domain in one line with the main entities in parentheses.
4. Print exactly this block (label column padded to 15 chars):

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <language>
Framework:     <framework> <version>
Dependencies:  <comma-separated runtime deps>
Domain:        <one-line domain (entities)>
Architecture:  <classification — one-line justification>
Source files:  <N> files analyzed
DB tables:     <comma-separated tables>
Entry point:   <file> (<run command>) — port <port>
Endpoints:     <N> routes
================================
```

Continue immediately to Phase 2 (same turn).

---

## PHASE 2 — ARCHITECTURE AUDIT

1. Read `references/02-antipattern-catalog.md` and `references/03-audit-report-template.md`.
2. For **every** catalog entry (AP-01 … AP-19), run the detection signals / grep sheet for the
   detected stack, then open the hit sites to confirm. Collect findings with **exact
   `file:line` or `file:start-end`** locations. One finding per (file, anti-pattern) cluster; list
   the individual lines inside the description. Classify severity per catalog; you may adjust one
   level with a one-line justification.
3. Cross-check the minimums: at least 5 findings and at least 1 CRITICAL/HIGH are expected for any
   legacy project. If you have fewer, re-run the grep sheet before concluding.
4. Build the report **strictly** following the template: header, `## Summary` counts,
   `## Findings` sorted CRITICAL → HIGH → MEDIUM → LOW (then by file path), `## Deprecated APIs`
   table (or "None detected for this stack."), `## Refactoring Plan (preview)` (mode, target tree,
   contract to preserve), `Total: N findings`. Summary counts must equal the number of findings.
5. Save the report to the report path (rule 7). This write does not touch any source file.
6. Print, in your final message of this turn: the Phase 1 block (if not already in this same
   message), the full report, and then **exactly**:

```
Report saved to: <path>

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

7. **STOP HERE. End the turn immediately after that line. No tool calls after it.** Do not proceed
   even if the invoking prompt or arguments say to continue automatically — the human must review
   the report first.

### Handling the answer (next user message)
- `y` / `yes` / `sim` / `s` → run Phase 3.
- `n` / `no` / `não` → print `Refactoring cancelled. Report kept at <path>.` and stop.
- Anything else → repeat the question and stop.
- If reference files are no longer in context (compaction / resumed session), re-read them.

---

## PHASE 3 — MVC REFACTORING (only after explicit confirmation)

1. Read `references/04-mvc-guidelines.md`, `references/05-refactoring-playbook.md` and
   `references/06-validation-runbook.md`.
2. **Preflight** (runbook §1–§3): note `git status --porcelain` (warn if dirty, continue); set up
   the toolchain (venv / `npm install`); pick a free port; run the **baseline**: boot the ORIGINAL
   app in the background, call every route from the inventory, record `status + top-level keys`
   per route, then kill it.
3. Pick the refactoring **mode** from the Phase 1 classification (guidelines §4):
   `Monolith decomposition`, `Partial-layering gap-fill` or `Fix-only`. Print the target tree
   before editing.
4. **Refactor** in this order, applying the playbook patterns (P1–P15) that fix the audit findings:
   1. `config` module reading environment variables **with safe defaults** (the app must boot with
      no `.env`) + `.env.example`;
   2. error classes + **centralized error handler** + logger;
   3. database access module (scoped connection / promisified wrapper / transactions);
   4. models per domain (persistence + invariants, parameterised queries, whitelist serializers);
   5. services only where multi-model use-cases, transactions or external gateways exist;
   6. controllers (thin: parse → validate → call service/model → respond);
   7. routes/blueprints/routers + composition root — **entry point keeps its path and run command**;
   8. delete superseded flat modules / god classes / dead code (never leave `models.py` next to
      `models/`); grep for stale imports;
   9. security fixes (P2, P4, P5, P6), deprecated-API modernization (P13), N+1 (P11), integrity
      (P14), readability (P15);
   10. update the project README run/config section (env vars, run command).
5. **Preserve the contract** (guidelines §5): every METHOD+PATH, success status codes and top-level
   response keys, error status codes/messages and envelope key, seed scripts and seeded
   credentials. Allowed deviations are only security-driven (removing leaked sensitive fields,
   guarding privileged endpoints with a token from env) and must be listed in the final block.
6. **Validate** (runbook §4–§7): boot the refactored app in the background (`DEBUG=false`, free
   port, admin token set when applicable), poll readiness, call every route in the same order as
   the baseline, compare, run the re-audit grep pass, kill the server, clean PID/log files.
7. If a check fails: read the log tail, fix, re-validate (max 3 loops). Never finish with an app
   that does not boot.
8. Print the completion block (runbook §7) in the final message:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<tree of the project, excluding .venv node_modules __pycache__ .claude reports .git>

## Validation
  ✓ Application boots without errors (port <p>, <t>s)
  ✓ All endpoints respond correctly (<ok>/<total> — see table)
  ✓ Zero CRITICAL/HIGH anti-patterns remaining (<n> LOW accepted)

## Endpoint check
| METHOD | PATH | baseline | after | keys match |
| ... |

## Contract changes (security-driven)
- <route>: <what changed and why>

## Next steps
- Review the diff and commit the refactored code
- Report kept at <report path>
================================
```

Use `✗` plus a `## Failed checks` section (with the log tail) if something could not be fixed.
