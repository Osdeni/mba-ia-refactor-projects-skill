# 03 — Audit Report Template (Phase 2)

## Rules

1. Labels and section headers are fixed (English, exactly as below). Free text (Description,
   Impact, Recommendation) is written in the project's README language.
2. Findings are sorted **CRITICAL → HIGH → MEDIUM → LOW**, then by file path, then by line.
3. Every finding has an exact location: `File: path:line` or `File: path:start-end`. When the same
   anti-pattern repeats in one file, use one finding with the main range and list the other lines
   inside Description (e.g. `também em :92, :140, :155`).
4. `## Summary` counts must equal the number of `###` findings per severity; `Total:` is their sum.
5. Each finding names its catalog ID (`AP-nn`) and its recommended playbook pattern (`P-n`).
6. `## Deprecated APIs` is always present: a table, or the sentence
   `None detected for this stack.`
7. `## Refactoring Plan (preview)` states the mode, the target structure and the contract size so
   the human can decide at the gate.
8. The report is saved as a Markdown file (path rule in SKILL.md) **and** printed in full in the
   final message of the turn, followed by the gate lines.

## Template

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <project directory name>
Stack:   <Language> + <Framework> <version>
Files:   <N> analyzed | ~<LOC> lines of code

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [CRITICAL] <Anti-pattern name> (AP-nn)
File: <path>:<line|start-end>
Description: <what was found, quoting the offending symbol/snippet; other occurrences>
Impact: <why it matters for security, correctness, maintainability or performance>
Recommendation: <fix> (playbook P-n)

### [HIGH] ...

### [MEDIUM] ...

### [LOW] ...

## Deprecated APIs
| Usage | Location | Modern equivalent |
|---|---|---|
| `datetime.utcnow()` | models/task.py:15 | `datetime.now(timezone.utc)` |

## Refactoring Plan (preview)
Mode: <Monolith decomposition | Partial-layering gap-fill | Fix-only>
Target structure:
<short tree of the directories/modules to be created or kept>
Contract to preserve: <N> endpoints (METHOD+PATH, status codes, top-level keys), error envelope `<key>`, run command `<cmd>`
Security-driven contract changes expected: <list or "none">

================================
Total: <N> findings
================================
```

## Gate (printed right after the report, then END THE TURN)

```
Report saved to: <path>

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

No tool calls may follow the gate line in the same turn.

## Example finding (for calibration)

```
### [CRITICAL] SQL Injection — string-built queries (AP-02)
File: models.py:109-111
Description: `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"` — entrada do usuário concatenada na query. Mesmo padrão em :28, :47-50, :57-61, :92, :126-129, :289-297.
Impact: Bypass de autenticação (`senha = "x' OR '1'='1"`) e leitura/alteração arbitrária do banco; qualquer apóstrofo derruba a rota com 500.
Recommendation: Usar placeholders `?` com tupla de parâmetros em todas as queries; montar filtros dinâmicos com listas de cláusulas + parâmetros (playbook P2).
```
