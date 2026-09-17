================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python 3.12 + Flask 3.0.0 (Flask-SQLAlchemy 3.1.1, Flask-Cors 4.0.0)
Files:   15 analyzed | ~1158 lines of code

## Summary
CRITICAL: 5 | HIGH: 9 | MEDIUM: 17 | LOW: 12

## Findings

### [CRITICAL] Hardcoded credentials & configuration (AP-01)
File: app.py:11-13
Description: `app.config['SECRET_KEY'] = 'super-secret-key-123'` (:13), URI do banco fixa `'sqlite:///tasks.db'` (:11) e `app.run(debug=True, host='0.0.0.0', port=5000)` (:34). Nenhum `os.environ`/`os.getenv` em todo o projeto; `python-dotenv` está em `requirements.txt` mas nunca é importado; não existe `.env.example`.
Impact: A chave de sessão vai para o histórico do git e é idêntica em todos os ambientes; banco, host e porta não podem variar sem editar código.
Recommendation: Criar módulo `config.py` lendo `SECRET_KEY`, `DATABASE_URL`, `HOST`, `PORT`, `DEBUG`, `CORS_ORIGINS` do ambiente com defaults seguros, carregado via `python-dotenv`, e adicionar `.env.example` (playbook P1).

### [CRITICAL] Sensitive data exposure (AP-05)
File: models/user.py:16-25
Description: `User.to_dict()` inclui `'password': self.password` (:21). O método é devolvido diretamente em `routes/user_routes.py:33` (GET /users/<id>), `:85` (POST /users), `:129` (PUT /users/<id>) e `:209` (POST /login → chave `user`).
Impact: O hash MD5 de todo usuário é exposto pela API pública; combinado com AP-04, equivale a entregar a senha.
Recommendation: Serializer whitelist (`to_dict` sem `password`), mantendo as demais chaves de resposta (playbook P5). Mudança de contrato de segurança a ser listada na Fase 3.

### [CRITICAL] Weak or plaintext credential storage (AP-04)
File: models/user.py:27-32
Description: `set_password` grava `hashlib.md5(pwd.encode()).hexdigest()` (:29) e `check_password` compara o MD5 com `==` (:32) — sem salt, sem KDF, comparação não constante. `seed.py:19,26,33` cadastra senhas de 4 caracteres (`'1234'`, `'abcd'`, `'pass'`); `routes/user_routes.py:64,115` aceita mínimo de 4 caracteres.
Impact: MD5 sem salt é quebrado por rainbow table em segundos; um dump do banco equivale a um dump de senhas. Senhas de 4 caracteres tornam brute force trivial.
Recommendation: Usar `werkzeug.security.generate_password_hash`/`check_password_hash` com verify-and-upgrade para os hashes MD5 legados (usuários do seed continuam logando e são migrados no primeiro login) (playbook P4).

### [CRITICAL] Unprotected privileged or dangerous endpoints (AP-06)
File: routes/user_routes.py:185-211
Description: `POST /login` devolve `'token': 'fake-jwt-token-' + str(user.id)` (:210) — token previsível e nunca verificado por nenhuma rota. Não há `before_request`, decorator ou header de autenticação em lugar algum: `POST /users` aceita `role` do cliente e permite auto-registro como `admin` (:52,:71); `PUT /users/<id>` altera senha/role/active de qualquer usuário (:92-132); `DELETE /users/<id>` (:134), `DELETE /tasks/<id>` (`task_routes.py:225`) e `DELETE /categories/<id>` (`report_routes.py:211`) são destrutivos e abertos.
Impact: Qualquer cliente anônimo pode virar admin, trocar senhas alheias e apagar usuários, tasks e categorias. O "login" transmite falsa sensação de segurança.
Recommendation: Emitir token assinado (`itsdangerous`, já dependência do Flask) mantendo a chave `token`; guardar operações privilegiadas (role/active, DELETE de usuário) com token admin lido de `ADMIN_TOKEN` no ambiente (playbook P6).

### [CRITICAL] Hardcoded credentials & configuration (AP-01)
File: services/notification_service.py:7-10
Description: Credenciais SMTP embutidas no construtor: `self.email_host = 'smtp.gmail.com'`, `self.email_user = 'taskmanager@gmail.com'`, `self.email_password = 'senha123'`.
Impact: Senha de e-mail versionada em texto claro; qualquer pessoa com acesso ao repositório pode usar a conta. O serviço nem sequer é usado, mas o segredo já vazou.
Recommendation: Mover para `SMTP_HOST/SMTP_PORT/SMTP_USER/SMTP_PASSWORD` no `config.py`; como o serviço é código morto, removê-lo ou reescrevê-lo como gateway injetável (playbook P1, P15).

### [HIGH] No centralized error handling / exception swallowing (AP-09)
File: app.py:1-34
Description: Nenhum `@app.errorhandler` registrado. Erros 404 de rota inexistente e 405 retornam HTML do Flask em vez do envelope `{error}`; `request.get_json()` sem `silent=True` (11 chamadas nas rotas) levanta `415 Unsupported Media Type` em HTML quando falta o `Content-Type`; exceções não capturadas viram página de debug (ver AP-10).
Impact: Contrato de erro inconsistente (JSON em uns casos, HTML em outros); com `debug=True` o traceback é enviado ao cliente.
Recommendation: Classes de erro (`NotFound`, `ValidationError`, `Conflict`, `Unauthorized`) + um handler central que responde `{error: msg}` com o status certo, incluindo handler para `HTTPException` (404/405/415) e genérico 500 com log (playbook P9).

### [HIGH] Global mutable state / shared connection (AP-08)
File: app.py:9-31
Description: `app = Flask(__name__)` criado no nível do módulo com configuração inline (:9-16) e `db.create_all()` executado em tempo de import (:30-31). Não existe app factory; `seed.py:2` faz `from app import app, db`, disparando a criação do schema como efeito colateral do import. `services/notification_service.py:6` guarda `self.notifications = []` em memória na instância.
Impact: Impossível instanciar a app com outra configuração (testes, outro banco); todo import tem efeito colateral no disco; estado em memória se perde entre processos e workers.
Recommendation: `create_app(config)` como composition root; `create_all()` dentro da factory ou em comando explícito; serviços injetados (playbook P8).

### [HIGH] Insecure runtime defaults (AP-10)
File: app.py:15-34
Description: `CORS(app)` sem lista de origens (:15) e `app.run(debug=True, host='0.0.0.0', port=5000)` (:34) como único caminho de execução.
Impact: Debugger do Werkzeug exposto em todas as interfaces (execução remota de código via console do debugger) e CORS aberto para qualquer origem.
Recommendation: `DEBUG`, `HOST`, `PORT`, `CORS_ORIGINS` vindos do `config.py` com defaults seguros (`DEBUG=false`, `HOST=127.0.0.1`) (playbook P1).

### [HIGH] Business logic in route handlers (AP-07)
File: routes/report_routes.py:12-101
Description: `summary_report` tem 90 linhas: 15 queries, cálculo de atraso inline (:33-43), agregação de produtividade por usuário (:53-68) e montagem do JSON. `user_report` (:103-155) repete o padrão com contadores manuais. O mesmo módulo ainda hospeda o CRUD de categorias (:157-223) com `db.session.add/commit/rollback` dentro dos handlers (:182-188, :204-209, :217-223).
Impact: Regras de relatório não são testáveis sem HTTP nem reutilizáveis; o módulo mistura dois domínios (reports e categories).
Recommendation: `ReportService` (agregações) + `Category` model com persistência; controllers finos; blueprint `category_routes.py` separado (playbook P7, P3).

### [HIGH] No centralized error handling / exception swallowing (AP-09)
File: routes/report_routes.py:186-221
Description: `except:` nu em :186, :207, :221 devolvendo mensagens genéricas 500 sem registrar a causa. `update_category` (:196) chama `request.get_json()` sem checar `None`: body vazio com `Content-Type: application/json` gera `TypeError: argument of type 'NoneType' is not iterable` → 500 não tratado.
Impact: Falhas reais (constraint, disco) ficam invisíveis; entrada ruim vira 500 em vez de 400.
Recommendation: Remover try/except locais; deixar exceções de domínio subirem ao handler central; validar body antes de usar (playbook P9, P12).

### [HIGH] Business logic in route handlers (AP-07)
File: routes/task_routes.py:11-299
Description: `get_tasks` (:11-63, 53 linhas) serializa manualmente, calcula `overdue` e busca usuário/categoria por task; `create_task` (:85-154, 70 linhas) faz validação de título/status/prioridade/FKs/data/tags, monta o model, persiste e loga; `update_task` (:156-223) repete tudo; `search_tasks` (:240-271) monta a query dinâmica; `task_stats` (:273-299) agrega. Todas as rotas importam `db` e chamam `db.session.commit()` diretamente.
Impact: Handlers gordos e duplicados; nenhuma regra (status válido, prioridade 1-5, FK existente, atraso) é reutilizável ou testável isoladamente.
Recommendation: `validators/task_validator.py` + métodos no `Task` model (`create`, `update`, `search`, `stats`, `to_dict(include=...)`) + `TaskController` fino (parse → validar → chamar → responder) (playbook P7, P12).

### [HIGH] No centralized error handling / exception swallowing (AP-09)
File: routes/task_routes.py:62-236
Description: `except:` nu em :62 (envolve todo o `get_tasks`, engolindo até `KeyboardInterrupt`), :137, :204, :236; `except Exception as e` em :151 e :221 apenas com `print`. Erros de conversão (`int(priority)` :261, `priority < 1` com string :113) não são tratados e caem no handler padrão.
Impact: Diagnóstico impossível em produção; mensagens de erro divergentes para o mesmo problema (`'Formato de data inválido. Use YYYY-MM-DD'` vs `'Formato de data inválido'`).
Recommendation: Substituir por exceções de domínio + handler central; logger em vez de `print` (playbook P9).

### [HIGH] Business logic in route handlers (AP-07)
File: routes/user_routes.py:42-183
Description: `create_user` (:42-90) valida nome/email/senha/role com regex inline, checa unicidade, cria e persiste; `update_user` (:92-132) repete as mesmas validações com mensagens ligeiramente diferentes (`'Senha muito curta'` vs `'Senha deve ter no mínimo 4 caracteres'`); `delete_user` (:134-151) apaga tasks manualmente em loop; `get_user_tasks` (:153-183) serializa e calcula atraso inline.
Impact: Regras de usuário espalhadas e divergentes entre create/update; impossível reutilizar em CLI, testes ou seed.
Recommendation: `validators/user_validator.py`, métodos de persistência no `User`, `AuthService` para login, `UserController` fino (playbook P7, P12).

### [HIGH] No centralized error handling / exception swallowing (AP-09)
File: routes/user_routes.py:87-149
Description: `except Exception as e` com `print(f"ERRO: {str(e)}")` (:87-90) e `except:` nu em :130 e :149, todos convertendo qualquer falha em 500 genérico; `IntegrityError` de e-mail duplicado (race entre a checagem :67 e o commit :82) vira `'Erro ao criar usuário'` em vez de 409.
Impact: Causa raiz perdida; status incorreto para conflitos de integridade.
Recommendation: Handler central mapeando `IntegrityError` → 409 e removendo os blocos locais (playbook P9).

### [MEDIUM] Deprecated / legacy API usage (AP-14)
File: app.py:12-34
Description: `app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False` (:12) já é o default no Flask-SQLAlchemy 3; `app.run(debug=True)` como servidor (:34); `flask-cors==4.0.0` (`requirements.txt:3`) abaixo da 6.x recomendada pelo advisory de private-network.
Impact: Configuração redundante e dependência com advisory conhecido.
Recommendation: Remover a chave, usar `flask run`/servidor WSGI, atualizar `flask-cors` (playbook P13).

### [MEDIUM] Data integrity gaps (AP-16)
File: models/task.py:13-21
Description: `user_id` e `category_id` são `ForeignKey` sem `ondelete` (:13-14) e os `relationship`s não definem `cascade` (:20-21); `PRAGMA foreign_keys` nunca é ativado no SQLite, então as FKs não são impostas. `routes/user_routes.py:140-142` contorna isso apagando tasks em loop manual.
Impact: Apagar categoria (`report_routes.py:218`) deixa `category_id` órfão nas tasks; a integridade depende de código de rota em vez do schema.
Recommendation: Ativar `PRAGMA foreign_keys=ON` no evento `connect` do engine; `ondelete='CASCADE'` para user→tasks e `ondelete='SET NULL'` para category→tasks com `passive_deletes=True` (playbook P14).

### [MEDIUM] Deprecated / legacy API usage (AP-14)
File: models/task.py:15-52
Description: `datetime.utcnow` usado como default de coluna (:15-16) e em `is_overdue` (:52). Mesmo uso em `models/user.py:14`, `models/category.py:11`, `seed.py:66-74`, `utils/helpers.py:38`, `services/notification_service.py:35`. Deprecado desde Python 3.12 (`DeprecationWarning`).
Impact: Warnings hoje, remoção em versão futura; datetimes naive dificultam qualquer suporte a fuso.
Recommendation: `datetime.now(timezone.utc)` centralizado em um helper `utcnow()` que devolve naive UTC para manter o schema (playbook P13).

### [MEDIUM] N+1 queries (AP-12)
File: routes/report_routes.py:15-163
Description: `summary_report` executa 12 `COUNT` separados (:15-28) que um único `GROUP BY status`/`GROUP BY priority` resolve, carrega todas as tasks (:30) só para contar atrasadas, e faz `Task.query.filter_by(user_id=u.id).all()` por usuário dentro do loop (:56). `get_categories` faz `Task.query.filter_by(category_id=c.id).count()` por categoria (:163).
Impact: Custo linear em usuários/categorias por requisição; com 1.000 usuários são 1.000 queries num único GET.
Recommendation: Agregações com `func.count` + `group_by`, `outerjoin` para totais por usuário/categoria (playbook P11).

### [MEDIUM] Duplicated logic (AP-13)
File: routes/report_routes.py:33-151
Description: Cálculo de atraso (`due_date < utcnow and status not in (done, cancelled)`) reimplementado em :33-37 e :132-135 embora `Task.is_overdue()` exista (`models/task.py:50`); `completion_rate` calculado inline em :67 e :151 enquanto `calculate_percentage` é importado de `utils.helpers` (:7) e nunca usado; contagem por status feita por `if/elif` manual (:119-127).
Impact: Três implementações da mesma regra que podem divergir.
Recommendation: Usar `Task.is_overdue()`/expressão SQL única e `calculate_percentage`, ou apagar o helper (playbook P12).

### [MEDIUM] Deprecated / legacy API usage (AP-14)
File: routes/report_routes.py:105-213
Description: `Model.query.get()` (legacy Query API, `LegacyAPIWarning` no SQLAlchemy 2.x) em :105, :192, :213; `Model.query.filter_by/count/all` em :15-56, :109, :159, :163; `datetime.utcnow()` em :35, :42, :45, :71, :133; `request.get_json()` sem `silent=True` em :169, :196.
Impact: Warnings hoje, quebra na próxima major; 415 em HTML para requests sem Content-Type.
Recommendation: `db.session.get()`, `db.session.scalars(select(...))`, `get_json(silent=True)` (playbook P13).

### [MEDIUM] Missing or inconsistent input validation (AP-15)
File: routes/report_routes.py:169-202
Description: `create_category` não valida tipo/tamanho de `name` nem o formato de `color` (:173-180); `update_category` usa `data` sem checar `None` (:196-202) e aceita qualquer valor para `color`.
Impact: `color` inválida quebra o schema `String(7)` silenciosamente (SQLite não impõe tamanho); body vazio gera 500.
Recommendation: Validator de categoria (nome obrigatório/string, cor `#rrggbb`) devolvendo 400 com as mensagens atuais (playbook P12).

### [MEDIUM] Data integrity gaps (AP-16)
File: routes/report_routes.py:211-223
Description: `delete_category` apaga a categoria sem tratar as tasks que a referenciam; `create_category` (:167-188) não valida unicidade de `name` nem o formato de `color` (`utils/helpers.py:52` tem `is_valid_color` que ninguém chama).
Impact: Tasks apontam para `category_id` inexistente e `GET /tasks` passa a devolver `category_name: null` silenciosamente; categorias duplicadas.
Recommendation: Regra explícita (SET NULL via FK) e validação de cor/nome no validator (playbook P14, P12).

### [MEDIUM] Duplicated logic (AP-13)
File: routes/task_routes.py:17-215
Description: Serialização de task copiada de `Task.to_dict()` (:17-28); regra de atraso repetida em :30-39, :71-80, :284-287; lista de status válidos duplicada em :110 e :177 (também em `models/task.py:39` e `utils/helpers.py:75,110`); validação de título/prioridade duplicada entre `create_task` (:96-114) e `update_task` (:166-184); tratamento de `tags` duplicado (:140-144, :209-213).
Impact: Qualquer alteração de regra exige tocar 4-6 lugares; mensagens já divergem.
Recommendation: `Task.to_dict()` como fonte única com `overdue`, validator único para create/update (playbook P12).

### [MEDIUM] N+1 queries (AP-12)
File: routes/task_routes.py:41-57
Description: `get_tasks` chama `User.query.get(t.user_id)` (:42) e `Category.query.get(t.category_id)` (:51) para cada task da lista, ignorando os `relationship`s já definidos no model. `task_stats` (:275-281) faz 5 `COUNT` + carrega todas as tasks para contar atrasadas.
Impact: 1 + 2N queries por listagem.
Recommendation: `selectinload(Task.user, Task.category)` ou `joinedload`; `GROUP BY status` e `COUNT` com filtro de atraso no SQL (playbook P11).

### [MEDIUM] Deprecated / legacy API usage (AP-14)
File: routes/task_routes.py:42-285
Description: `Model.query.get()` em :42, :51, :67, :117, :122, :158, :188, :195, :227; `Task.query.filter_by/count/all` em :14, :247-281; `datetime.utcnow()` em :31, :72, :215, :285; `request.get_json()` sem `silent=True` em :87, :162; `type(x) == list` em :141, :210 em vez de `isinstance`.
Impact: Idem acima.
Recommendation: Modernização por arquivo conforme tabela (playbook P13).

### [MEDIUM] Missing or inconsistent input validation (AP-15)
File: routes/task_routes.py:96-264
Description: `len(title)` sem checar tipo (:96) → `TypeError` se `title` for número; `priority < 1` sem coerção (:113, :182) → `TypeError: '<' not supported between 'str' and 'int'` → 500; `int(priority)`/`int(user_id)` em `search_tasks` sem tratamento (:261, :264) → `ValueError` → 500; `tags` que não seja lista nem string é gravado como está (:140-144); `q` interpolado em `LIKE` sem escapar `%`/`_` (:252-253).
Impact: Entrada malformada derruba a rota com 500 em vez de 400.
Recommendation: Validator com coerção e mensagens 400 (`'Prioridade deve ser entre 1 e 5'`), escapar wildcards do LIKE (playbook P12).

### [MEDIUM] N+1 queries (AP-12)
File: routes/user_routes.py:22
Description: `'task_count': len(u.tasks)` dentro do `for u in users` dispara o lazy load do backref por usuário. `get_user` (:35) e `get_user_tasks` (:159) consultam tasks separadamente em vez de usar `user.tasks`.
Impact: 1 + N queries em `GET /users`.
Recommendation: Subquery `COUNT` agrupada por `user_id` em `outerjoin` (playbook P11).

### [MEDIUM] Deprecated / legacy API usage (AP-14)
File: routes/user_routes.py:29-197
Description: `User.query.get()` em :29, :94, :136, :155; `Model.query.filter_by/all` em :12, :35, :67, :109, :140, :159, :197; `datetime.utcnow()` em :172; `request.get_json()` sem `silent=True` em :44, :98, :187.
Impact: Idem acima.
Recommendation: Idem (playbook P13).

### [MEDIUM] Duplicated logic (AP-13)
File: routes/user_routes.py:61-180
Description: Regex de e-mail repetida em :61 e :106 (e em `utils/helpers.py:21`); lista de roles em :71 e :120 (e `helpers.py:111`); serialização manual de usuário (:15-23) e de task (:162-169) em vez de `to_dict()`; regra de atraso reimplementada em :171-180.
Impact: Mesma regra em três arquivos com risco de drift.
Recommendation: `validators/user_validator.py` + serializers do model (playbook P12).

### [MEDIUM] Missing or inconsistent input validation (AP-15)
File: routes/user_routes.py:61-125
Description: Regex `^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$` aceita `a@b` (:61, :106); `name` sem validação de tipo/tamanho no update (:102-103); `active` aceita qualquer valor (`"sim"`, `0`) sem coerção para bool (:124-125); `password` sem checagem de tipo antes de `len()` (:64, :115).
Impact: Dados inconsistentes no banco e 500 para tipos inesperados.
Recommendation: Validator único para create/update com regex de e-mail mais estrita e coerção de `active` (playbook P12).

### [MEDIUM] Duplicated logic (AP-13)
File: utils/helpers.py:19-108
Description: `validate_email` (:19), `parse_date` (:43), `is_valid_color` (:52) e `process_task_data` (:57-108) implementam exatamente as validações que as rotas reescrevem inline, porém nenhuma dessas funções é chamada em lugar algum; `parse_date` aceita também `dd/mm/yyyy`, formato que as rotas rejeitam.
Impact: Duas versões da mesma validação, uma delas morta e com comportamento diferente.
Recommendation: Promover os helpers a validators usados pelos controllers ou removê-los (playbook P12, P15).

### [LOW] Code hygiene (AP-19)
File: app.py:7
Description: `import os, sys, json, datetime` — `os`, `sys` e `json` nunca usados; `datetime` só para o `/health`.
Impact: Ruído e falsa impressão de que há configuração via `os`.
Recommendation: Remover imports mortos (playbook P15).

### [LOW] Code hygiene (AP-19)
File: models/user.py:34-38
Description: `is_admin` escrito como `if ...: return True else: return False`; mesmo padrão em `models/task.py:38-48` (`validate_status`, `validate_priority`) e aninhamento de 4 níveis em `is_overdue` (`models/task.py:50-60`); nenhum desses métodos é chamado pelas rotas.
Impact: Legibilidade; métodos de model ignorados sinalizam que as regras vivem no lugar errado.
Recommendation: `return self.role == 'admin'`; guard clauses; usar os métodos nos validators (playbook P15).

### [LOW] Code hygiene — dead dependencies (AP-19)
File: requirements.txt:4-6
Description: `marshmallow==3.20.1`, `requests==2.31.0` e `python-dotenv==1.0.0` declarados mas nunca importados em nenhum arquivo `.py`.
Impact: Instalação mais lenta e superfície de dependências sem uso.
Recommendation: Remover `marshmallow` e `requests`; passar a usar `python-dotenv` no `config.py` (playbook P15).

### [LOW] Code hygiene (AP-19)
File: routes/report_routes.py:7-8
Description: `format_date` e `calculate_percentage` importados e nunca usados (:7); `import json` morto (:8).
Impact: Ruído.
Recommendation: Remover ou usar (playbook P15).

### [LOW] Cryptic or inconsistent naming (AP-18)
File: routes/report_routes.py:10-223
Description: Módulo `report_routes.py` hospeda o CRUD de `/categories` (:157-223) sob o blueprint `'reports'`; variáveis `p1..p5` (:24-28), `t`, `u`, `c`, `cat` em todos os loops; em `seed.py` `u1..u3`, `c1..c4`, `td`.
Impact: Nome do arquivo engana quem procura o CRUD de categorias; loops ilegíveis.
Recommendation: `routes/category_routes.py` separado; nomes descritivos (`task`, `user`, `category`) (playbook P15).

### [LOW] Magic numbers / strings (AP-17)
File: routes/report_routes.py:45-129
Description: `timedelta(days=7)` (:45), rótulos `critical/high/medium/low/minimal` mapeados por posição (:84-88), `priority <= 2` como "alta prioridade" (:129), `'#000000'` como cor padrão (:180 e `models/category.py:10`).
Impact: Regras de negócio implícitas; mudar a janela de "recente" exige caçar literais.
Recommendation: `utils/constants.py` (`RECENT_DAYS`, `PRIORITY_LABELS`, `HIGH_PRIORITY_MAX`, `DEFAULT_COLOR`) — `utils/helpers.py:110-116` já define constantes que ninguém usa (playbook P15).

### [LOW] Code hygiene (AP-19)
File: routes/task_routes.py:7-234
Description: `import json, os, sys, time` sem uso (:7); `print` como log em :149, :153, :219, :234; aninhamento de 4 níveis para `overdue` (:30-39, :71-80); `if/else` para atribuir `None` (:41-57).
Impact: Sem níveis de log, sem timestamp, sem destino configurável.
Recommendation: `logging.getLogger(__name__)`; guard clauses (playbook P15).

### [LOW] Magic numbers / strings (AP-17)
File: routes/task_routes.py:96-113
Description: Limites `3` e `200` do título (:96, :99, :167, :169), intervalo `1..5` de prioridade (:113, :182), lista de status inline (:110, :177), default `3` (:104), formato `'%Y-%m-%d'` (:136, :203).
Impact: Constantes já existem em `utils/helpers.py:110-116` (`MIN_TITLE_LENGTH`, `MAX_TITLE_LENGTH`, `VALID_STATUSES`, `DEFAULT_PRIORITY`) e são ignoradas.
Recommendation: Centralizar em `utils/constants.py` e consumir nos validators/models (playbook P15).

### [LOW] Code hygiene (AP-19)
File: routes/user_routes.py:6-147
Description: `import hashlib, json, re` — `hashlib` e `json` sem uso (:6); `print` como log em :83, :89, :147; aninhamento de 4 níveis em :171-180.
Impact: Idem.
Recommendation: Logger + guard clauses (playbook P15).

### [LOW] Magic numbers / strings (AP-17)
File: routes/user_routes.py:64-120
Description: `len(password) < 4` (:64, :115), lista `['user', 'admin', 'manager']` inline (:71, :120), regex de e-mail duplicada (:61, :106), prefixo `'fake-jwt-token-'` (:210).
Impact: Política de senha e roles espalhadas em literais.
Recommendation: `MIN_PASSWORD_LENGTH`, `VALID_ROLES`, `EMAIL_REGEX` em `utils/constants.py` (playbook P15).

### [LOW] Code hygiene — dead code (AP-19)
File: services/notification_service.py:4-48
Description: `NotificationService` nunca é importado nem instanciado; `send_email` abre conexão SMTP síncrona real com credenciais fixas (:12-25); `get_notifications` percorre lista em memória (:43-48).
Impact: Código morto que carrega segredo (AP-01) e distrai; `services/` fica com aparência de camada existente sem função.
Recommendation: Remover o módulo; se notificação for necessária no futuro, reescrever como gateway configurável e injetado (playbook P15).

### [LOW] Code hygiene — dead code (AP-19)
File: utils/helpers.py:1-116
Description: Imports mortos `os, json, sys, math, hashlib` (:3-7); `generate_id` (:31), `log_action` (:36, usa `print`), `sanitize_string` (:25), `process_task_data` (:57) e todas as demais funções nunca são chamadas; `except:` nu em :46, :49, :88.
Impact: Módulo "gaveta" inteiro sem uso; constantes úteis (:110-116) desperdiçadas.
Recommendation: Reorganizar em `utils/constants.py`, `utils/dates.py` e `validators/`, apagando o resto (playbook P15).

## Deprecated APIs
| Usage | Location | Modern equivalent |
|---|---|---|
| `datetime.utcnow()` | models/task.py:15-16,52; models/user.py:14; models/category.py:11; routes/task_routes.py:31,72,215,285; routes/user_routes.py:172; routes/report_routes.py:35,42,45,71,133; seed.py:66-74; utils/helpers.py:38; services/notification_service.py:35 | `datetime.now(timezone.utc)` (naive UTC via `.replace(tzinfo=None)` para manter o schema) |
| `hashlib.md5` para senhas | models/user.py:29,32 | `werkzeug.security.generate_password_hash` / `check_password_hash` |
| `Model.query.get(id)` (legacy Query API) | routes/task_routes.py:42,51,67,117,122,158,188,195,227; routes/user_routes.py:29,94,136,155; routes/report_routes.py:105,192,213 | `db.session.get(Model, id)` |
| `Model.query.filter_by(...)/all()/count()` | routes/task_routes.py:14,247-281; routes/user_routes.py:12,35,67,109,140,159,197; routes/report_routes.py:15-56,109,159,163; seed.py:11-13,94-96 | `db.session.scalars(select(Model).where(...))` / `db.session.scalar(select(func.count()))` |
| `request.get_json()` sem `silent=True` (levanta 415) | routes/task_routes.py:87,162; routes/user_routes.py:44,98,187; routes/report_routes.py:169,196 | `request.get_json(silent=True)` + validação de `None` |
| `SQLALCHEMY_TRACK_MODIFICATIONS = False` | app.py:12 | Remover (default no Flask-SQLAlchemy 3) |
| `app.run(debug=True)` como servidor | app.py:34 | `flask run` em dev; gunicorn/waitress em prod; `DEBUG` via env |
| `type(x) == list` | routes/task_routes.py:141,210; utils/helpers.py:103 | `isinstance(x, list)` |
| `flask-cors==4.0.0` | requirements.txt:3 | `flask-cors>=6` |

## Refactoring Plan (preview)
Mode: Partial-layering gap-fill
Target structure:
```
task-manager-api/
├── app.py                      # entry point mantido: create_app() + app = create_app(); python app.py
├── config.py                   # env vars com defaults seguros (SECRET_KEY, DATABASE_URL, HOST, PORT, DEBUG, CORS_ORIGINS, ADMIN_TOKEN)
├── .env.example
├── database.py                 # db = SQLAlchemy() + PRAGMA foreign_keys + utcnow()
├── errors.py                   # AppError/NotFound/ValidationError/Conflict/Unauthorized + register_error_handlers
├── models/
│   ├── __init__.py
│   ├── user.py                 # invariantes, hash KDF + upgrade de MD5, to_dict whitelist
│   ├── task.py                 # to_dict(with_overdue/with_names), create/update/search/stats
│   └── category.py
├── services/
│   ├── auth_service.py         # login + token assinado (itsdangerous) + admin guard
│   └── report_service.py       # agregações multi-model (summary, user report)
├── controllers/
│   ├── health_controller.py
│   ├── user_controller.py
│   ├── task_controller.py
│   ├── category_controller.py
│   └── report_controller.py
├── routes/
│   ├── __init__.py             # register_blueprints(app)
│   ├── user_routes.py
│   ├── task_routes.py
│   ├── category_routes.py      # extraído de report_routes.py
│   └── report_routes.py
├── validators/
│   ├── user_validator.py
│   ├── task_validator.py
│   └── category_validator.py
├── utils/
│   ├── constants.py            # VALID_STATUSES, VALID_ROLES, limites, PRIORITY_LABELS, RECENT_DAYS
│   └── dates.py                # utcnow(), parse_date()
├── seed.py                     # mantido (mesmas credenciais seed)
├── requirements.txt            # sem marshmallow/requests
└── README.md                   # seção de configuração/execução atualizada
```
Removidos: `services/notification_service.py`, `utils/helpers.py`.
Contract to preserve: 22 endpoints (METHOD+PATH, status codes, top-level keys), error envelope `error`, run command `python app.py` (porta 5000 por padrão), `python seed.py` com as mesmas credenciais (joao@email.com/1234, maria@email.com/abcd, pedro@email.com/pass).
Security-driven contract changes expected:
- Remover a chave `password` das respostas de `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e do objeto `user` em `POST /login` (AP-05).
- `POST /login` passa a devolver um token assinado em vez de `fake-jwt-token-<id>` (mesma chave `token`) (AP-06).
- `DELETE /users/<id>` e alteração de `role`/`active` em `POST/PUT /users` exigem header `X-Admin-Token` igual a `ADMIN_TOKEN` do ambiente; sem o header, `role` é forçado para `user` no cadastro e a operação privilegiada responde 401/403 `{error}` (AP-06).

================================
Total: 43 findings
================================
