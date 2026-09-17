# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.
Refatorada para o padrão MVC: `config → database → models → services → controllers → routes`.

## Como rodar

```bash
npm install
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e já carrega seeds automaticamente no boot
(usuário `leonan@fullcycle.com.br` / senha `123`, cursos "Clean Architecture" e "Docker", uma matrícula paga).

Exemplos de requisições estão em `api.http`.

## Configuração (variáveis de ambiente)

Todas as variáveis têm default — a aplicação sobe sem `.env`. Copie `.env.example` para `.env` para personalizar.

| Variável | Default | Descrição |
|---|---|---|
| `NODE_ENV` | `development` | Ambiente de execução |
| `DEBUG` | `false` | `true` mostra stack trace no log e a mensagem original em erros 500 |
| `HOST` | `0.0.0.0` | Interface de escuta |
| `PORT` | `3000` | Porta HTTP |
| `DB_FILE` | `:memory:` | Arquivo SQLite (`:memory:` recria banco + seeds a cada boot) |
| `ADMIN_TOKEN` | *(vazio)* | Token do header `X-Admin-Token` para rotas administrativas; sem valor elas respondem 403 |
| `PAYMENT_GATEWAY_KEY` | chave de teste | Chave do gateway de pagamento (nunca a chave live em dev) |
| `LOG_LEVEL` | `info` | `error`, `warn`, `info` ou `debug` |
| `JSON_BODY_LIMIT` | `100kb` | Tamanho máximo do corpo JSON |

Exemplo:

```bash
ADMIN_TOKEN=meu-token PORT=4000 npm start
```

## Endpoints

| Método | Rota | Auth | Respostas |
|---|---|---|---|
| `POST` | `/api/checkout` | — | 200 `{msg, enrollment_id}` · 400 `Bad Request` / `Pagamento recusado` · 404 `Curso não encontrado` |
| `GET` | `/api/admin/financial-report` | `X-Admin-Token` | 200 `[{course, revenue, students[{student, paid}]}]` · 401/403 |
| `DELETE` | `/api/users/:id` | `X-Admin-Token` | 200 `Usuário deletado` · 404 `Usuário não encontrado` · 401/403 |

Corpo do checkout: `{ "usr", "eml", "pwd", "c_id", "card" }`. Cartões iniciados por `4` são aprovados (gateway simulado).
`pwd` é obrigatório apenas quando o e-mail ainda não existe (novos usuários não recebem mais senha padrão).
Erros são devolvidos em texto puro; falhas internas respondem `500 Erro interno`.

## Estrutura

```
src/
├── app.js            # composition root (createApp + start)
├── config/           # variáveis de ambiente com defaults seguros
├── database/         # conexão sqlite3 promisificada, schema (FK/cascade), seeds
├── errors/           # AppError e subclasses (400/401/403/404)
├── middlewares/      # asyncHandler, errorHandler, notFound, requireAdmin
├── models/           # persistência por entidade (queries parametrizadas)
├── services/         # checkout (transação), gateway de pagamento, relatório (JOIN)
├── controllers/      # parse → validate → service → respond
├── routes/           # mapeamento URL → controller
├── validators/       # validação de entrada
└── utils/            # logger com mascaramento, constantes, hashing scrypt
```

Caminho de upgrade: Express 5 propaga erros de handlers async nativamente, dispensando o `asyncHandler`.
