# Skill `refactor-arch` — Auditoria e Refatoração Arquitetural Automatizada

Solução do desafio **"Criação de Skills — Refatoração Arquitetural Automatizada"** do MBA em Engenharia de Software com IA (FullCycle).
Enunciado original: [repositório base devfullcycle/mba-ia-refactor-projects-skill](https://github.com/devfullcycle/mba-ia-refactor-projects-skill).

Ferramenta escolhida: **Claude Code** (Custom Skills em `.claude/skills/refactor-arch/`).

Sumário:
1. [Análise Manual](#1-análise-manual)
2. [Construção da Skill](#2-construção-da-skill)
3. [Resultados](#3-resultados)
4. [Como Executar](#4-como-executar)

Acompanhamento da execução (checklist por etapa): [`PLANO.md`](PLANO.md).

---

## 1. Análise Manual

Escala usada (definida no desafio): **CRITICAL** (segurança/arquitetura que expõe dados ou quebra a separação de responsabilidades), **HIGH** (violações fortes de MVC/SOLID), **MEDIUM** (duplicação, N+1, validação ausente), **LOW** (legibilidade, nomes, magic numbers).

### 1.1 `code-smells-project/` — Python/Flask 3.1.1, API de E-commerce (4 arquivos, ~780 linhas, 19 rotas)

| # | Severidade | Problema | Onde | Por que é relevante |
|---|---|---|---|---|
| 1 | CRITICAL | Endpoint `POST /admin/query` executa SQL arbitrário vindo do body, sem autenticação | `app.py:59-78` | Qualquer cliente pode ler/apagar o banco inteiro (`DROP TABLE`, `SELECT * FROM usuarios`). Também é lógica de banco dentro do arquivo de rotas. |
| 2 | CRITICAL | SQL Injection por concatenação de strings em praticamente todas as queries | `models.py:28,60,68,92,110,128` | `POST /login` com `senha = "x' OR '1'='1"` autentica como admin (`models.py:110`). Um apóstrofo em `nome` derruba a rota com 500. |
| 3 | CRITICAL | Senhas armazenadas em texto puro e devolvidas pela API | `database.py:76-79`, `models.py:83,99` | `GET /usuarios` lista a senha de todos os usuários. Sem hash, um dump do banco é um dump de credenciais. |
| 4 | CRITICAL | `SECRET_KEY` hardcoded e vazada pelo `/health`, com `DEBUG=True` em `0.0.0.0` | `app.py:7-8,88`, `controllers.py:285-289` | Segredo no git e exposto por HTTP; o debugger do Werkzeug ligado em todas as interfaces é execução remota de código. |
| 5 | HIGH | Conexão SQLite global única com `check_same_thread=False` e sem `rollback` | `database.py:4-10`, `models.py:148-168` | Estado global mutável compartilhado por requisições concorrentes; uma exceção no meio de `criar_pedido` deixa transação aberta que a próxima requisição commita. |
| 6 | HIGH | `except Exception as e: return jsonify({"erro": str(e)}), 500` repetido em 15 handlers, sem error handler central | `controllers.py:10,21,60,95,...,291` | Vaza mensagens internas de SQL ao cliente, transforma erros 400/415 em 500 e impede tratamento uniforme. |
| 7 | MEDIUM | Queries N+1 na listagem de pedidos (1 + N pedidos + N×M itens) | `models.py:171-233` | 100 pedidos com 5 itens = ~600 queries; um `JOIN` resolve. As duas funções são cópias idênticas (só muda o `WHERE`). |
| 8 | MEDIUM | Validação duplicada e já divergente entre criar e atualizar produto | `controllers.py:24-62` vs `64-96` | O `PUT` aceita nome de 1 caractere e categoria inválida que o `POST` rejeita. Não há checagem de tipo (`preco: "abc"` vira 500). |
| 9 | LOW | Filtros usam truthiness: `if preco_min:` ignora `0`; `if termo:` ignora string vazia | `models.py:290,294`, `controllers.py:118` | `preco_min=0` é silenciosamente descartado. Deveria ser `is not None`. |
| 10 | LOW | Magic numbers das faixas de desconto (`10000/5000/1000`, `0.1/0.05/0.02`) no data layer | `models.py:257-262` | Regra de negócio de preço enterrada em código de acesso a dados, sem nome e sem teste. |
| 11 | LOW | Parâmetro `id` sombreando builtin e `print` como log (incluindo e-mails) | `models.py:24,54,65,89`; `controllers.py:161,179,182` | Legibilidade e vazamento de PII em stdout. |

### 1.2 `ecommerce-api-legacy/` — Node.js/Express 4, LMS API com checkout (3 arquivos, 180 linhas, 3 rotas)

| # | Severidade | Problema | Onde | Por que é relevante |
|---|---|---|---|---|
| 1 | CRITICAL | Credenciais e chave de pagamento `pk_live_...` hardcoded em objeto de config | `src/utils.js:1-7` | Segredos de produção commitados; nada lê `process.env`. |
| 2 | CRITICAL | Número completo do cartão e chave do gateway escritos em `console.log` | `src/AppManager.js:45` | Violação PCI: dados de cartão em qualquer agregador de logs. |
| 3 | CRITICAL | "Hash" de senha `badCrypto` = base64 truncado, e seed com senha em texto puro `'123'` | `src/utils.js:17-23`, `src/AppManager.js:18` | Reversível e com colisões triviais; usuários criados sem `pwd` recebem a senha padrão `"123456"` (`AppManager.js:68`). |
| 4 | CRITICAL | God class `AppManager`: cria o banco, faz seed, define rotas, valida, processa pagamento e persiste | `src/AppManager.js:4-141` | Zero separação de camadas: impossível testar sem subir Express + banco. É o alvo principal da refatoração. |
| 5 | HIGH | Callback hell (5 níveis) sem transação no checkout, e relatório com contadores manuais | `src/AppManager.js:37-77`, `86-121` | Falha no `INSERT` de pagamento deixa matrícula órfã; erros ignorados em vários callbacks (`:57,104,106,133`). |
| 6 | HIGH | Sem middleware de erro, sem 404, sem `unhandledRejection` | `src/app.js:1-14` | `card` numérico (`4111...` sem aspas) gera `cc.startsWith is not a function` e derruba o processo. |
| 7 | HIGH | Estado global mutável exportado (`globalCache`, `totalRevenue`) | `src/utils.js:9-10,25` | Cache sem limite (vazamento de memória) que ninguém lê; `totalRevenue` exportado por valor nunca muda. |
| 8 | MEDIUM | N+1 no relatório financeiro (1 + N cursos + N×M matrículas × 2) | `src/AppManager.js:83-128` | Cresce multiplicativamente; um `JOIN` com `GROUP BY` resolve. Ainda ignora `active` e lê só o primeiro pagamento. |
| 9 | MEDIUM | Validação incompleta: só presença de 4 campos, `pwd` não validado, `c_id` sem tipo | `src/AppManager.js:35` | Dados inválidos chegam ao SQL e ao gateway; senha padrão silenciosa. |
| 10 | MEDIUM | `DELETE /api/users/:id` ignora erro, sempre 200, deixa matrículas e pagamentos órfãos | `src/AppManager.js:131-137` | A própria mensagem de resposta admite o bug. Sem FK, sem cascade. |
| 11 | LOW | Nomes crípticos `u, e, p, cid, cc` (`e` parece "error") e `const self = this` misturado com arrow functions | `src/AppManager.js:26,29-33` | Dificulta leitura e refatoração segura. |
| 12 | LOW | Magic strings/numbers: `"4"` decide aprovação, `"123456"`, `10000` iterações, porta `3000` | `src/AppManager.js:46,68`, `src/utils.js:6,19` | Regras de negócio sem nome. |
| 13 | LOW | Import morto (`totalRevenue`), `let` para bindings nunca reatribuídos, nome `AppManager` sem significado | `src/AppManager.js:2,4` | Código morto e nomenclatura que não comunica responsabilidade. |

### 1.3 `task-manager-api/` — Python/Flask 3.0.0 + Flask-SQLAlchemy, API de Task Manager (17 arquivos, ~1170 linhas, 22 rotas)

Projeto já tem `models/`, `routes/`, `services/`, `utils/`, mas as rotas concentram validação, regra de negócio, persistência e serialização; `services/` e boa parte de `utils/` são código morto.

| # | Severidade | Problema | Onde | Por que é relevante |
|---|---|---|---|---|
| 1 | CRITICAL | `SECRET_KEY` e senha SMTP hardcoded | `app.py:13`, `services/notification_service.py:7-10` | Segredos no git; `python-dotenv` está no `requirements.txt` mas nunca é usado. |
| 2 | CRITICAL | Senhas com MD5 sem salt e hash devolvido pela API (`to_dict` inclui `password`) | `models/user.py:21,29,32` | Hash exposto em `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `POST /login`; MD5 é quebrável por GPU/rainbow table. |
| 3 | CRITICAL | `debug=True` em `0.0.0.0`, `CORS(app)` irrestrito e nenhum endpoint exige autenticação (`/login` devolve `fake-jwt-token-<id>`) | `app.py:15,34`, `routes/user_routes.py:185-211` | Debugger remoto + qualquer site pode chamar `DELETE /users/<id>` anonimamente. |
| 4 | HIGH | Lógica de negócio pesada nas rotas (relatório de 90 linhas, criação/atualização de task com validação duplicada) | `routes/report_routes.py:12-101`, `routes/task_routes.py:85-223` | Rotas fazem parse + validação + regra + ORM + serialização; nada é testável isoladamente. `Task.is_overdue()` e `utils/helpers.process_task_data()` existem e nunca são chamados. |
| 5 | HIGH | `except:` nu em 8 pontos, sem log, sem error handler central; sem app factory (`db.create_all()` em import) | `routes/task_routes.py:62,137,204,236`, `routes/user_routes.py:130,149`, `routes/report_routes.py:186,207,221`, `app.py:30-31` | Erros reais viram 500 opaco; importar `app` cria o banco (efeito colateral). |
| 6 | MEDIUM | Queries N+1: `User.query.get`/`Category.query.get` por task, `len(u.tasks)` por usuário, uma query por usuário no relatório | `routes/task_routes.py:42,51`, `routes/user_routes.py:22`, `routes/report_routes.py:53-68` | Os relacionamentos já existem no modelo; `joinedload`/`GROUP BY` resolvem. |
| 7 | MEDIUM | APIs deprecated: `datetime.utcnow()` (Python 3.12) e `Model.query.get()` (SQLAlchemy 2.0 legacy) | `models/task.py:15-16,52`, `models/user.py:14`, `routes/*.py` (~60 usos), `seed.py` | Gera `DeprecationWarning`/`LegacyAPIWarning` hoje e será removido; datetimes naive são inseguros para timezone. |
| 8 | MEDIUM | Regra de "overdue" copiada 6 vezes com `if/else` aninhado, e whitelist de status em 5 lugares | `routes/task_routes.py:30-39,71-80,281-287`, `routes/user_routes.py:171-180`, `routes/report_routes.py:34-37,132-135` | Uma das cópias já divergiu; fonte única de verdade violada. |
| 9 | LOW | Imports não usados em bloco (`os, sys, json, datetime` / `json, os, sys, time`) | `app.py:7`, `routes/task_routes.py:7`, `utils/helpers.py:3-7` | Ruído e dependências fantasmas (`marshmallow`, `requests` no requirements sem uso). |
| 10 | LOW | Magic numbers: `3`/`200` (título), `4` (senha), `7` dias, `1..5` prioridade — enquanto `utils/helpers.py:110-116` já define as constantes sem usá-las | `routes/task_routes.py:96,99`, `routes/user_routes.py:64,115`, `routes/report_routes.py:45` | Regras espalhadas e inconsistentes. |
| 11 | LOW | `type(tags) == list` em vez de `isinstance`, nomes de uma letra (`t, u, c, p1..p5`), `report_routes.py` hospedando CRUD de categorias | `routes/task_routes.py:141,210`, `routes/report_routes.py:157-223` | Legibilidade e módulo mal nomeado. |

---

## 2. Construção da Skill

A skill vive em `<projeto>/.claude/skills/refactor-arch/` (cópias idênticas nos 3 projetos) e é invocada com `claude "/refactor-arch"` (ou `claude -p "/refactor-arch <caminho-do-relatório>"` em modo headless).

### 2.1 Estrutura e decisões de design

```
.claude/skills/refactor-arch/
├── SKILL.md                              # o prompt: regras gerais + 3 fases sequenciais (174 linhas)
└── references/
    ├── 01-project-analysis.md            # Fase 1 — heurísticas de linguagem/framework/DB/entry point, inventário de rotas, classificação da arquitetura
    ├── 02-antipattern-catalog.md         # Fase 2 — catálogo de 19 anti-patterns (AP-01..AP-19) com sinais por stack + grep sheet
    ├── 03-audit-report-template.md       # Fase 2 — template verbatim do relatório + texto do gate
    ├── 04-mvc-guidelines.md              # Fase 3 — camadas, direção de dependências, layouts alvo Flask/Express, modos adaptativos, contrato
    ├── 05-refactoring-playbook.md        # Fase 3 — 15 padrões de transformação (P1..P15) com antes/depois em Python e JS
    └── 06-validation-runbook.md          # Fase 3 — venv/npm, porta livre, boot em background, smoke test, comparação baseline, teardown
```

Decisões principais:

- **SKILL.md é um prompt curto; o conhecimento fica nos `references/`.** Cada fase diz exatamente qual arquivo ler naquele momento (lazy loading), o que mantém o contexto pequeno e permite evoluir o catálogo/playbook sem tocar no fluxo.
- **Gate de confirmação por fim de turno.** A Fase 2 grava o relatório, imprime `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]` e a instrução é explícita: "STOP, end the turn, no tool calls after this line". Isso funciona igual no modo interativo e no headless (`claude -p` + `--resume <session_id> "y"`). Nenhum arquivo-fonte é tocado antes do "y" — o único arquivo escrito é o relatório.
- **Saída pensada para headless.** Como `claude -p` só mostra a última mensagem do turno, a skill exige que a mensagem final do turno 1 contenha o bloco da Fase 1 + relatório completo + gate, e a do turno 2 contenha a validação + bloco de conclusão.
- **Inventário de rotas como contrato.** A Fase 1 produz uma tabela METHOD | PATH | handler | shape de sucesso | envelope de erro que a Fase 3 usa como "lista do que não pode quebrar", e o runbook compara baseline (app original) vs pós-refatoração rota a rota.
- **Modos adaptativos na Fase 3.** A classificação da Fase 1 (`Monolith` / `Partial layering` / `MVC-compliant`) escolhe entre *Monolith decomposition* (projetos 1 e 2), *Partial-layering gap-fill* (projeto 3: preserva `models/ routes/ services/ utils/` e adiciona `config/ controllers/ middlewares/ validators/`) e *Fix-only*.
- **Config via ambiente com defaults.** Regra explícita: o app precisa subir sem `.env`; segredos têm default de desenvolvimento com warning; endpoints perigosos continuam existindo, mas guardados por `ADMIN_TOKEN`.
- **Validação real, não declarativa.** O runbook obriga: venv/npm, porta livre, servidor em background com log + PID, readiness poll, curl em 100% das rotas, probes de erro (nunca 500), re-audit por grep, teardown garantido. "Never claim success for a check that was not executed."

### 2.2 Catálogo de anti-patterns (por que cada um entrou)

| ID | Anti-pattern | Sev. | Motivo de estar no catálogo |
|---|---|---|---|
| AP-01 | Hardcoded credentials & configuration | CRITICAL | Presente nos 3 projetos (SECRET_KEY, senha SMTP, `pk_live_...`). |
| AP-02 | SQL injection (string-built queries) | CRITICAL | Projeto 1 inteiro; inclui o caso de "SQL cru vindo do cliente". |
| AP-03 | God class / god module | CRITICAL | `models.py` (P1) e `AppManager.js` (P2) — o alvo central da refatoração MVC. |
| AP-04 | Weak or plaintext credential storage | CRITICAL | Texto puro (P1), `badCrypto` (P2), MD5 sem salt (P3). |
| AP-05 | Sensitive data exposure (responses & logs) | CRITICAL | Senha em `GET /usuarios`, `secret_key` no `/health`, cartão no `console.log`, hash no `to_dict`. |
| AP-06 | Unprotected privileged/dangerous endpoints | CRITICAL | `/admin/query`, `/admin/reset-db`, `DELETE /api/users/:id`, `DELETE /users/<id>` sem auth. |
| AP-07 | Business logic in route handlers | HIGH | Sintoma clássico de MVC quebrado nos 3 projetos. |
| AP-08 | Global mutable state / shared connection | HIGH | Conexão global `check_same_thread=False`, `globalCache`, `create_all()` em import. |
| AP-09 | No centralized error handling | HIGH | `except Exception: str(e)` ×15, `except:` nus, Express sem middleware de erro (processo morre). |
| AP-10 | Insecure runtime defaults | HIGH | `debug=True` + `0.0.0.0` + `CORS(app)` aberto. |
| AP-11 | Callback hell / no DI | HIGH | Pirâmide de 5 níveis no checkout do P2; `new Database()` no construtor. |
| AP-12 | N+1 queries | MEDIUM | Pedidos+itens (P1), relatório financeiro (P2), tasks/users (P3). |
| AP-13 | Duplicated logic | MEDIUM | Validação POST/PUT divergente, `overdue` copiado 6×, 7 serializers row→dict. |
| AP-14 | Deprecated / legacy API usage | MEDIUM | Exigência do desafio; tabela com equivalentes modernos para Python/Flask/SQLAlchemy e Node/Express. |
| AP-15 | Missing/inconsistent input validation | MEDIUM | `get_json()` sem guarda → 415/500, tipos não checados, `pwd` não validado. |
| AP-16 | Data integrity gaps | MEDIUM | Sem FK/cascade/transação: órfãos e pedidos parciais. |
| AP-17 | Magic numbers / strings | LOW | Faixas de desconto, `"4"` aprova cartão, `"123456"`. |
| AP-18 | Cryptic or inconsistent naming | LOW | `u, e, p, cid, cc`, `id` sombreando builtin, `report_routes.py` com CRUD de categorias. |
| AP-19 | Code hygiene | LOW | `print` como log, imports mortos, `services/` nunca usado, `type(x) == list`. |

Cada entrada traz **sinais de detecção separados para Python/Flask e Node/Express**, mais um *grep sheet* pronto por stack, para que o agente chegue à linha exata em vez de "achar" o problema.

### 2.3 Como a skill é agnóstica de tecnologia

1. **Detecção por evidência, não por suposição:** arquivos-marcador (`requirements.txt`, `package.json`, `go.mod`, …), versão lida do lockfile quando `node_modules` não existe, grep de imports.
2. **Catálogo com sinais por stack + conceito genérico:** o anti-pattern é definido pelo conceito (ex.: "query dentro de loop") e cada stack tem seus greps; stacks não previstas caem na definição conceitual.
3. **Playbook com exemplos em duas linguagens** (Python e JS) para cada um dos 15 padrões, mais uma seção "Other stacks" nas guidelines.
4. **Contrato comportamental em vez de estrutura fixa:** o que se preserva é METHOD+PATH, status, chaves top-level, envelope de erro e comando de execução — independentemente do framework.
5. **Runbook parametrizado:** receitas de boot para Flask e Node, porta escolhida em runtime, `PORT` via env.
6. **Testado nos 3 projetos** com a mesma cópia da skill (verificado com `diff -r`).

### 2.4 Desafios encontrados e como foram resolvidos

| Desafio | Solução |
|---|---|
| Pausar entre Fase 2 e 3 em modo headless (`claude -p` não tem prompt interativo) | Gate implementado como "terminar o turno na pergunta"; a continuação é `claude -p --resume <session_id> "y"`. Verificado: o turno 1 termina exatamente na pergunta e `git status` mostra apenas o relatório. |
| `claude -p` só exibe a última mensagem | Regra explícita no SKILL.md sobre o conteúdo obrigatório da mensagem final de cada turno. |
| Servidor em foreground trava a ferramenta; reloader do Flask deixa processo filho vivo | Receita obrigatória: `nohup ... & echo $! > pid`, readiness poll, `use_reloader=False`, teardown com `kill` + `pkill` de fallback. |
| Porta 5000 compartilhada pelos dois projetos Flask; 3000 fixa no Node | Seleção de porta livre com `ss -ltn` e `PORT` via env (a config extraída na Fase 3 passa a respeitar). |
| Flask não instalado globalmente; `sqlite3` do Node compila nativamente | Runbook cria `.venv` no projeto e usa `.venv/bin/python` sempre; `npm install` com timeout longo. |
| Senhas legadas (texto puro / MD5) em bancos existentes | Padrão P4: verify-and-upgrade — aceita hash moderno, MD5 e texto puro, e re-hasheia no login bem-sucedido; seeds passam a gerar hash. |
| Endpoints "originais devem responder" vs. endpoints perigosos (`/admin/query`) | Rotas mantidas, guardadas por `X-Admin-Token` (`ADMIN_TOKEN` de env) e `/admin/query` restrito a `SELECT`; listado como "contract change (security-driven)". |
| Relatório precisa ficar em `reports/` na raiz do repositório, mas a skill roda dentro do projeto | Argumento opcional: `/refactor-arch ../reports/audit-project-N.md` (+ `--add-dir ../reports` no headless). Default: `reports/audit-<projeto>.md` dentro do projeto. |
| `claude` aninhado dentro de uma sessão Claude Code | `env -u CLAUDECODE claude -p ...` e `--model` explícito. |

## 3. Resultados

Execução real da skill nos 3 projetos, em modo headless (`claude -p`), com o modelo `claude-fable-5-1`. Toda a saída das fases está em `reports/logs/project-N-phase1-2.log` (Fase 1 + relatório + gate) e `reports/logs/project-N-phase3.log` (refatoração + validação da própria skill). A validação **independente** (script de `curl` rodado por fora da skill, contra o app original e contra o refatorado) está em `reports/logs/project-N-validation.log`.

### 3.1 Resumo dos relatórios de auditoria

| Projeto | Stack detectada (Fase 1) | CRITICAL | HIGH | MEDIUM | LOW | Total | Relatório |
|---|---|---|---|---|---|---|---|
| 1 — code-smells-project | Python 3.12 + Flask 3.1.1 · Monolith · 4 arquivos · 19 rotas | 8 | 5 | 5 | 3 | **21** | [`reports/audit-project-1.md`](reports/audit-project-1.md) |
| 2 — ecommerce-api-legacy | JavaScript (Node 24) + Express 4.22.1 · Monolith · 3 arquivos · 3 rotas | 5 | 5 | 5 | 3 | **18** | [`reports/audit-project-2.md`](reports/audit-project-2.md) |
| 3 — task-manager-api | Python 3.12 + Flask 3.0.0 + Flask-SQLAlchemy · Partial layering · 15 arquivos · 22 rotas | 5 | 9 | 17 | 12 | **43** | [`reports/audit-project-3.md`](reports/audit-project-3.md) |

Cruzamento com a análise manual (seção 1): a Fase 2 encontrou **todos** os problemas listados manualmente nos 3 projetos (11/11, 13/13 e 11/11), sempre com `arquivo:linha`, e adicionou outros (ex.: `request.get_json()` sem `silent=True`, `flask-cors` desatualizado, `SELECT *`, falta de índices/UNIQUE). Os 3 relatórios incluem a seção `## Deprecated APIs` com equivalente moderno para cada uso.

### 3.2 Estrutura antes / depois

**Projeto 1 — code-smells-project** (modo *Monolith decomposition*)

```
ANTES                          DEPOIS
app.py  (rotas + SQL inline)   app.py                 composition root: create_app(), registra blueprints e error handlers
controllers.py (15 handlers)   config/settings.py     SECRET_KEY, DEBUG, HOST, PORT, DB_PATH, ADMIN_TOKEN, CORS_ORIGINS via env
models.py (SQL + regras)       database/              connection.py (flask.g + teardown + PRAGMA FK), schema.py, seed.py
database.py (conexão global)   models/                produto_model, usuario_model, pedido_model (queries parametrizadas), serializers
                               services/              pedido, relatorio, auth, usuario, admin, notificacao
                               controllers/           produto, usuario, auth, pedido, relatorio, health, home, admin (finos)
                               routes/                blueprints: produto, usuario, pedido, relatorio, sistema
                               middlewares/           error_handler.py (AppError/HTTPException/Exception), auth.py (require_admin)
                               validators/            produto, usuario, pedido (mensagens originais preservadas)
                               errors.py, constants.py, utils/{logger,security}.py, .env.example, .gitignore
```

**Projeto 2 — ecommerce-api-legacy** (modo *Monolith decomposition*)

```
ANTES                          DEPOIS (tudo em src/)
src/app.js                     app.js                 composition root: express.json → routes → notFound → errorHandler; listen só se main
src/AppManager.js (god class)  config/index.js        PORT, DB_FILE, PAYMENT_GATEWAY_KEY, ADMIN_TOKEN, LOG_LEVEL via process.env (frozen)
src/utils.js (config+cache+    database/              connection.js (sqlite3 promisificado + withTransaction), schema.js (FK ON DELETE CASCADE), seed.js
  "crypto")                    models/                user, course, enrollment, payment, auditLog
                               services/              checkoutService (transação), paymentGateway (cartão mascarado), reportService (1 JOIN)
                               controllers/           checkout, user, admin
                               routes/                index.js (/api), checkoutRoutes, userRoutes, adminRoutes
                               middlewares/           asyncHandler, errorHandler (4 args), notFound, requireAdmin
                               errors/AppError.js, utils/{crypto (scrypt), logger, constants}.js, validators/checkoutValidator.js, .env.example
```

**Projeto 3 — task-manager-api** (modo *Partial-layering gap-fill* — pacotes existentes preservados)

```
ANTES                          DEPOIS
app.py (create_all em import)  app.py                 create_app() + app module-level (seed.py continua com `from app import app, db`)
database.py                    database.py            (mantido)
models/{task,user,category}    models/                mantidos; User.to_dict sem password; hashing scrypt c/ upgrade de MD5; Task.is_overdue com guard clauses
routes/{task,user,report}      routes/                task, user, category (separado de report), report, health — só mapeamento URL→controller
  (validação+regra+ORM+        controllers/           task, user, category, report, health (NOVO)
   serialização nas rotas)     services/              notification (config-driven), auth, report, task (NOVO: auth/report/task)
services/notification (morto)  validators/            task, user, category (NOVO — substitui utils/helpers.process_task_data, nunca usado)
utils/helpers.py (morto)       middlewares/           error_handler.py, auth.py (NOVO)
                               config/settings.py, errors.py, utils/{constants,dates,logger}.py, .env.example (NOVO); utils/helpers.py removido
```

### 3.3 Checklist de validação (preenchido)

| Item | P1 | P2 | P3 |
|---|---|---|---|
| **Fase 1** — Linguagem detectada corretamente | ✅ | ✅ | ✅ |
| Framework detectado corretamente (com versão) | ✅ Flask 3.1.1 | ✅ Express 4.22.1 | ✅ Flask 3.0.0 |
| Domínio da aplicação descrito corretamente | ✅ E-commerce (produtos, pedidos, usuários) | ✅ LMS com checkout | ✅ Task Manager (tasks, users, categories) |
| Número de arquivos analisados condiz com a realidade | ✅ 4 | ✅ 3 | ✅ 15 |
| **Fase 2** — Relatório segue o template | ✅ | ✅ | ✅ |
| Cada finding tem arquivo e linhas exatos | ✅ | ✅ | ✅ |
| Findings ordenados por severidade | ✅ | ✅ | ✅ |
| Mínimo de 5 findings | ✅ 21 | ✅ 18 | ✅ 43 |
| Detecção de APIs deprecated incluída | ✅ | ✅ | ✅ |
| Skill pausa e pede confirmação antes da Fase 3 | ✅ turno termina em `[y/n]`; `git status` só mostra o relatório | ✅ | ✅ |
| **Fase 3** — Estrutura de diretórios segue MVC | ✅ | ✅ | ✅ |
| Configuração extraída para módulo de config | ✅ `config/settings.py` | ✅ `src/config/index.js` | ✅ `config/settings.py` |
| Models criados para abstrair dados | ✅ | ✅ | ✅ (mantidos e corrigidos) |
| Views/Routes separadas | ✅ blueprints | ✅ routers | ✅ blueprints finos |
| Controllers concentram o fluxo | ✅ | ✅ | ✅ |
| Error handling centralizado | ✅ `middlewares/error_handler.py` | ✅ `middlewares/errorHandler.js` | ✅ `middlewares/error_handler.py` |
| Entry point claro | ✅ `app.py` | ✅ `src/app.js` (`npm start`) | ✅ `app.py` + `seed.py` |
| Aplicação inicia sem erros (inclusive sem `.env`) | ✅ | ✅ | ✅ |
| Endpoints originais respondem corretamente | ✅ 19/19 | ✅ 3/3 | ✅ 22/22 |

### 3.4 Logs das aplicações rodando após a refatoração

Trechos de `reports/logs/project-N-validation.log` (status HTTP e chaves top-level por rota; baseline = app original):

```
# Projeto 1 — code-smells-project (após)
GET    /health        200  ['ambiente', 'counts', 'database', 'status', 'versao']   # antes incluía secret_key, debug, db_path
GET    /usuarios      200  ['dados', 'sucesso']                                     # ocorrências de "senha": 0 (antes: 4)
POST   /login (senha "x' OR '1'='1")   401                                          # antes: 200 (bypass por SQL injection)
POST   /produtos ({"preco":"abc"})     400  ['erro', 'sucesso']                     # antes: 500
PUT    /pedidos/999999/status          404  ['erro', 'sucesso']                     # antes: 200 "sucesso"
POST   /admin/reset-db sem token       401                                          # antes: 200 (banco apagado por qualquer um)

# Projeto 2 — ecommerce-api-legacy (após)
POST   /api/checkout                   200  ['enrollment_id', 'msg']
POST   /api/checkout (card numérico)   400  text:Bad Request                        # antes: TypeError derrubava o processo
GET    /api/nope                       404  text:Not Found
alive=200                                                                          # antes: 000 (processo morto)
log do servidor: "Processando cartão ****4444 (chave test)"                         # antes: número completo + pk_live_...

# Projeto 3 — task-manager-api (após)
GET    /users/1       200  ['active', 'created_at', 'email', 'id', 'name', 'role', 'tasks']   # antes incluía password
POST   /tasks ({"priority":"2"})       201                                          # antes: 500 (TypeError str < int)
GET    /tasks/search?priority=abc      400  ['error']                               # antes: 500
PUT    /categories/1 (sem body)        400  ['error']                               # antes: 415 HTML
login com hash MD5 legado -> 200; hash migrado para scrypt:32768... no primeiro login
```

### 3.5 Observações sobre o comportamento da skill em stacks diferentes

- **Fase 1 foi precisa nas 3 stacks**, incluindo a versão resolvida do Express lida do `package-lock.json` (sem `node_modules`) e a distinção entre `sqlite3` stdlib e Flask-SQLAlchemy. No projeto 3 ela apontou corretamente que o `tasks.db` real fica em `instance/`.
- **A granularidade dos findings variou:** nos projetos 1 e 2 a skill agrupou por (arquivo, anti-pattern) como o catálogo pede (21 e 18 findings); no projeto 3, com 15 arquivos, ela abriu um finding por arquivo para o mesmo anti-pattern (43 findings). Ambos são válidos pelo template, mas mostra que a regra de agrupamento poderia ser mais rígida para projetos maiores.
- **Modo adaptativo funcionou:** projetos 1 e 2 receberam decomposição completa (arquivos planos apagados); o projeto 3 manteve `models/ routes/ services/ utils/` e só preencheu as lacunas, sem quebrar `seed.py`.
- **Node exigiu decisões específicas de plataforma** que o playbook previa: `asyncHandler` porque o Express 4 não propaga rejeições de promises; `scrypt` nativo do `crypto` para não adicionar dependências; wrapper promisificado sobre o `sqlite3` de callbacks; erros em texto puro para preservar o envelope original.
- **Python exigiu cuidado com compatibilidade de dados:** `datetime.utcnow()` → helper que devolve UTC naive, para os strings serializados não ganharem `+00:00`; verificação de senha aceita scrypt, MD5 e texto puro e migra no login, para bancos antigos continuarem funcionando.
- **Segurança vs. "endpoints originais respondem":** a skill manteve todas as rotas, inclusive `/admin/query`, mas atrás de `X-Admin-Token` e restrita a `SELECT`; listou cada mudança como *contract change (security-driven)*.
- **Headless:** o gate funcionou nas 3 execuções (o turno 1 terminou exatamente na pergunta, sem tocar código). Na Fase 3 do projeto 2 a sessão aninhada foi cortada por limite de uso da API (HTTP 429) no meio da refatoração; bastou `claude -p --resume <session_id>` pedindo para concluir a Fase 3, e a skill re-leu as referências, terminou e validou. Isso reforça a decisão de instruir "on resume, re-read the reference files".
- **Custo/tempo:** ~2–4 USD e 13–29 turnos por auditoria; ~2–7 USD e 39–55 turnos por refatoração+validação, com o modelo Fable 5.1.

## 4. Como Executar

### 4.1 Pré-requisitos

- [Claude Code](https://code.claude.com/docs) instalado e autenticado (`claude --version` — usado aqui: 2.1.273). A skill é um *Custom Skill* de projeto: basta a pasta `.claude/skills/refactor-arch/` existir no diretório em que o `claude` é iniciado.
- Python 3.12+ (`python3 -m venv` disponível) para os projetos Flask; Node.js 20+ e npm para o projeto Express.
- `curl` e `ss` (iproute2) — usados pelo runbook de validação.

### 4.2 Executar a skill em cada projeto

Modo interativo (o que o desafio pede):

```bash
# Projeto 1
cd code-smells-project
claude "/refactor-arch"            # Fase 1 + Fase 2 → relatório em reports/audit-code-smells-project.md (dentro do projeto)
# responda "y" quando aparecer: Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]

# Projeto 2
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3
cd ../task-manager-api
claude "/refactor-arch"
```

Para gravar o relatório direto na raiz do repositório, passe o caminho como argumento:
`claude "/refactor-arch ../reports/audit-project-1.md"`.

Modo headless (como esta entrega foi executada — um comando por fase, o gate vira o fim do turno):

```bash
cd code-smells-project
claude -p "/refactor-arch ../reports/audit-project-1.md" \
  --model claude-fable-5-1 --permission-mode acceptEdits \
  --allowedTools "Bash,Read,Write,Edit,MultiEdit,Glob,Grep" --add-dir ../reports \
  --output-format json > turn1.json          # Fases 1 e 2; termina na pergunta [y/n]

SID=$(python3 -c "import json;print(json.load(open('turn1.json'))['session_id'])")
claude -p --resume "$SID" "y" \
  --model claude-fable-5-1 --permission-mode acceptEdits \
  --allowedTools "Bash,Read,Write,Edit,MultiEdit,Glob,Grep" --add-dir ../reports \
  --output-format json > turn2.json          # Fase 3 + validação + bloco de conclusão
```

> Se estiver rodando o comando de dentro de outra sessão do Claude Code, prefixe com `env -u CLAUDECODE`.

### 4.3 Como validar que a refatoração funcionou

1. **Bloco de conclusão da skill** (`PHASE 3: REFACTORING COMPLETE`): traz a árvore nova, a tabela `baseline | after` por endpoint e a lista de mudanças de contrato motivadas por segurança. Os blocos completos desta entrega estão em `reports/logs/project-{1,2,3}-phase3.log`.
2. **Subir a aplicação refatorada** (sem `.env` ela sobe com defaults; `ADMIN_TOKEN` habilita as rotas administrativas):

```bash
# Projeto 1
cd code-smells-project && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
ADMIN_TOKEN=meu-token .venv/bin/python app.py          # http://127.0.0.1:5000
curl -s localhost:5000/produtos | head -c 200
curl -s -X POST localhost:5000/login -H 'Content-Type: application/json' -d '{"email":"admin@loja.com","senha":"admin123"}'
curl -s -X POST localhost:5000/admin/query -H 'X-Admin-Token: meu-token' -H 'Content-Type: application/json' -d '{"sql":"SELECT COUNT(*) AS n FROM produtos"}'

# Projeto 2
cd ecommerce-api-legacy && npm install
ADMIN_TOKEN=meu-token npm start                        # http://127.0.0.1:3000
curl -s -X POST localhost:3000/api/checkout -H 'Content-Type: application/json' \
  -d '{"usr":"Ana","eml":"ana@x.com","pwd":"segredo","c_id":2,"card":"4111222233334444"}'
curl -s localhost:3000/api/admin/financial-report -H 'X-Admin-Token: meu-token'

# Projeto 3
cd task-manager-api && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python seed.py && .venv/bin/python app.py    # http://127.0.0.1:5000
curl -s localhost:5000/tasks/stats
curl -s -X POST localhost:5000/login -H 'Content-Type: application/json' -d '{"email":"joao@email.com","password":"1234"}'
```

3. **Smoke test independente** (usado nesta entrega, fora da skill): `reports/logs/project-N-validation.log` contém, para cada projeto, a saída do mesmo script de `curl` rodado contra o app original (baseline) e contra o app refatorado — status HTTP e chaves top-level de cada rota, mais probes que antes retornavam 500 ou derrubavam o processo.
4. **Re-auditar**: rode `claude "/refactor-arch"` de novo no projeto refatorado; a Fase 2 não deve encontrar findings CRITICAL/HIGH.
