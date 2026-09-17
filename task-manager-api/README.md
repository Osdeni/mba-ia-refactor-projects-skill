# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. O projeto foi
refatorado para MVC: `config/` (variáveis de ambiente), `models/` (persistência e invariantes),
`validators/`, `services/` (login, tasks, relatórios, notificações), `controllers/` (finos),
`routes/` (blueprints) e `middlewares/` (error handler central e guarda administrativa).

## Como rodar

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python seed.py
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000` (host e porta configuráveis). O `seed.py` popula o
banco SQLite (`instance/tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do
primeiro boot**, caso contrário os endpoints vão retornar listas vazias.

Usuários do seed: `joao@email.com` / `1234` (admin), `maria@email.com` / `abcd` (user),
`pedro@email.com` / `pass` (manager). Bancos criados pela versão anterior continuam funcionando:
hashes MD5 legados são verificados e atualizados no primeiro login.

## Configuração

Todas as variáveis têm default; a app sobe sem `.env`. Copie `.env.example` para `.env` para
alterar:

| Variável | Default | Descrição |
|---|---|---|
| `SECRET_KEY` | `dev-only-change-me` | chave de assinatura do token de login (obrigatória em produção) |
| `DEBUG` | `false` | debugger do Flask |
| `HOST` / `PORT` | `127.0.0.1` / `5000` | bind do servidor de desenvolvimento |
| `CORS_ORIGINS` | `*` | origens permitidas (lista separada por vírgula) |
| `LOG_LEVEL` | `INFO` | nível de log |
| `DATABASE_URL` | `sqlite:///tasks.db` | URL SQLAlchemy do banco |
| `ADMIN_TOKEN` | *(vazio)* | token do header `X-Admin-Token` para operações administrativas |
| `TOKEN_MAX_AGE` | `86400` | validade (s) do token retornado por `POST /login` |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` | *(vazio)* | e-mail de notificação de task atribuída; sem `SMTP_HOST` apenas loga |

## Endpoints

| Método | Rota | Observação |
|---|---|---|
| GET | `/`, `/health` | |
| GET/POST | `/users` | `POST` com `role` diferente de `user` exige `X-Admin-Token` |
| GET/PUT/DELETE | `/users/<id>` | `PUT` de `role`/`active` e `DELETE` exigem `X-Admin-Token` |
| GET | `/users/<id>/tasks` | |
| POST | `/login` | retorna `token` assinado (`itsdangerous`) |
| GET/POST | `/tasks` | |
| GET/PUT/DELETE | `/tasks/<id>` | |
| GET | `/tasks/search?q=&status=&priority=&user_id=` | |
| GET | `/tasks/stats` | |
| GET/POST | `/categories` | |
| PUT/DELETE | `/categories/<id>` | apagar categoria deixa `category_id` das tasks como `null` |
| GET | `/reports/summary`, `/reports/user/<id>` | |

Erros são sempre JSON no formato `{"error": "<mensagem>"}`. Operações administrativas sem
`ADMIN_TOKEN` configurado respondem `403`; com token errado, `401`.

Para produção use um servidor WSGI (ex.: `gunicorn 'app:app'`) em vez de `python app.py`.
