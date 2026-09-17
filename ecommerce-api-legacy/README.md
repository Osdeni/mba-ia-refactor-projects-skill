# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.
Refatorada para MVC: `config → database → models → services → controllers → routes`, com
tratamento de erro centralizado e configuração por variáveis de ambiente.

## Como rodar

```bash
npm install
npm start          # node src/app.js
```

A aplicação sobe em `http://localhost:3000` por padrão. O banco SQLite é em memória e já carrega os
seeds automaticamente no boot (usuário `leonan@fullcycle.com.br` / senha `123`, cursos
"Clean Architecture" e "Docker").

## Configuração (variáveis de ambiente)

Todas as variáveis têm default — a app sobe sem `.env`. Copie `.env.example` para `.env` ou
exporte no shell:

| Variável | Default | Descrição |
|---|---|---|
| `NODE_ENV` | `development` | ambiente |
| `DEBUG` | `false` | `true` grava stack traces no log (nunca na resposta) |
| `HOST` | `0.0.0.0` | interface do servidor |
| `PORT` | `3000` | porta HTTP |
| `DB_FILE` | `:memory:` | arquivo SQLite (`:memory:` recria e popula a cada boot) |
| `ADMIN_TOKEN` | *(vazio)* | token exigido no header `X-Admin-Token` das rotas administrativas; vazio → 403 |
| `PAYMENT_GATEWAY_KEY` | chave de dev | chave do gateway de pagamento |
| `LOG_LEVEL` | `info` | `error` \| `warn` \| `info` \| `debug` |

Exemplo:

```bash
ADMIN_TOKEN=meu-token PORT=3000 npm start
```

## Endpoints

| Método | Rota | Auth | Sucesso |
|---|---|---|---|
| POST | `/api/checkout` | — | `200 {"msg":"Sucesso","enrollment_id":N}` |
| GET | `/api/admin/financial-report` | `X-Admin-Token` | `200 [{course, revenue, students:[{student, paid}]}]` |
| DELETE | `/api/users/:id` | `X-Admin-Token` | `200 "Usuário deletado"` (matrículas e pagamentos removidos em cascata) |

Erros são texto puro: `400 Bad Request` / `400 Pagamento recusado` / `404 Curso não encontrado` /
`404 Usuário não encontrado` / `401`/`403` nas rotas administrativas / `404 Not Found`.

Exemplos de requisições estão em `api.http`.

## Estrutura

```
src/
  app.js            # composition root (express.json, rotas, 404, errorHandler, listen)
  config/           # variáveis de ambiente com defaults seguros
  database/         # conexão SQLite promisificada, schema (FK + cascade), seeds, transação
  models/           # persistência por entidade (queries parametrizadas)
  services/         # casos de uso: checkout (transacional), gateway de pagamento, relatório
  controllers/      # parse → validar → serviço → resposta
  routes/           # mapeamento URL → controller (express.Router)
  middlewares/      # asyncHandler, errorHandler, notFound, requireAdmin
  validators/       # validação de entrada com as mensagens originais
  errors/           # AppError e subclasses
  utils/            # constants, crypto (scrypt), logger
```

Caminho de upgrade: Express 5 propaga erros assíncronos nativamente e dispensa o `asyncHandler`.
