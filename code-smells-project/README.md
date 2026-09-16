# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000`. O banco SQLite (`loja.db`) é criado automaticamente no
primeiro boot, já com produtos e usuários de exemplo (`admin@loja.com` / `admin123`,
`joao@email.com` / `123456`, `maria@email.com` / `senha123`). Senhas são gravadas com hash; bancos
antigos com senhas em texto puro continuam funcionando e são migrados no primeiro login.

## Configuração

Todas as variáveis são opcionais e têm default (veja `.env.example`):

| Variável | Default | Descrição |
|---|---|---|
| `SECRET_KEY` | `dev-only-change-me` | Segredo do Flask (defina em produção) |
| `DEBUG` | `false` | Ativa o debugger/reloader do servidor de desenvolvimento |
| `HOST` / `PORT` | `127.0.0.1` / `5000` | Endereço e porta do servidor |
| `DB_PATH` | `loja.db` | Caminho do arquivo SQLite |
| `ADMIN_TOKEN` | (vazio) | Token exigido no header `X-Admin-Token` das rotas `/admin/*`; vazio desabilita-as (403) |
| `CORS_ORIGINS` | `*` | Origens permitidas, separadas por vírgula |
| `LOG_LEVEL` | `INFO` | Nível de log |
| `APP_ENV` | `development` | Nome do ambiente exibido em `/health` |

Exemplo com rotas administrativas habilitadas:

```bash
ADMIN_TOKEN=meu-token python app.py
curl -X POST http://127.0.0.1:5000/admin/query -H 'X-Admin-Token: meu-token' \
     -H 'Content-Type: application/json' -d '{"sql": "SELECT COUNT(*) AS n FROM produtos"}'
```

`/admin/query` aceita apenas consultas `SELECT` (conexão somente leitura).

Para produção use um servidor WSGI (ex.: `gunicorn 'app:app'`) em vez de `python app.py`.

## Estrutura

```
app.py            # create_app() + execução (composition root)
config/           # settings lidas do ambiente com defaults
database/         # conexão por request, schema (com FKs) e seeds
models/           # persistência por entidade + serializadores whitelist
services/         # casos de uso (pedido, auth, relatório, admin, notificações)
validators/       # validação de entrada (mensagens da API)
controllers/      # handlers finos: parse → validate → service/model → resposta
routes/           # blueprints (URL → controller)
middlewares/      # handler central de erros e guarda admin
utils/            # logger e hash de senha
errors.py, constants.py
```

Erros seguem o envelope `{"erro": "<mensagem>", "sucesso": false}` com o status HTTP adequado.
