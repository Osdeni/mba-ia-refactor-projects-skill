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

_(preenchido na Etapa 6 — ver `PLANO.md`)_

## 3. Resultados

_(preenchido na Etapa 6 — ver `PLANO.md`)_

## 4. Como Executar

_(preenchido na Etapa 6 — ver `PLANO.md`)_
