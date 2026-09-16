# PLANO DE EXECUÇÃO — Desafio "Skill de Auditoria e Refatoração Arquitetural"

Fork: https://github.com/Osdeni/mba-ia-refactor-projects-skill
Regras: etapas evolutivas; máximo de 10 tentativas por etapa (o contador zera ao avançar); acima de 10, perguntar ao usuário.
Legenda: `[ ]` pendente · `[x]` concluído · `Tentativas: N`

---

## Etapa 0 — Bootstrap (Tentativas: 1)
- [x] Criar `PLANO.md` na raiz com checklist
- [x] Salvar memória de preferências de fluxo
- [x] Commit `docs: adiciona plano de execução do desafio`

## Etapa 1 — Análise Manual (README seção A) (Tentativas: 1)
- [x] code-smells-project: ≥5 problemas (≥1 CRITICAL/HIGH, ≥2 MEDIUM, ≥2 LOW) com arquivo:linha e justificativa
- [x] ecommerce-api-legacy: idem
- [x] task-manager-api: idem
- [x] Commit `docs: análise manual dos 3 projetos`

## Etapa 2 — Criação da Skill em `code-smells-project/.claude/skills/refactor-arch/` (Tentativas: 1)
- [x] `SKILL.md` com 3 fases sequenciais e gate de confirmação na Fase 2
- [x] `references/01-project-analysis.md` (análise de projeto)
- [x] `references/02-antipattern-catalog.md` (≥8 anti-patterns, 4 severidades, inclui APIs deprecated)
- [x] `references/03-audit-report-template.md` (template do relatório)
- [x] `references/04-mvc-guidelines.md` (guidelines de arquitetura MVC)
- [x] `references/05-refactoring-playbook.md` (≥8 padrões com antes/depois)
- [x] `references/06-validation-runbook.md` (validação: boot + endpoints)
- [x] Verificação objetiva: contagens mínimas + skill reconhecida pelo Claude Code
- [x] Commit `feat(skill): cria skill refactor-arch com referências`

## Etapa 3 — Execução no Projeto 1: code-smells-project (Tentativas: 1)
- [x] Rodar `/refactor-arch` (headless) — Fase 1 detecta Python/Flask e imprime resumo
- [x] Fase 2 gera relatório com ≥5 findings (≥1 CRITICAL/HIGH) e pausa pedindo confirmação
- [x] Confirmar Fase 3 — estrutura MVC criada
- [x] Aplicação inicia sem erros
- [x] Endpoints originais respondem (smoke test independente, log salvo)
- [x] Relatório salvo em `reports/audit-project-1.md`
- [x] Checklist de validação do projeto 1 preenchido (abaixo)
- [x] Commit `refactor(code-smells-project): aplica MVC via skill refactor-arch + relatório 1`

## Etapa 4 — Execução no Projeto 2: ecommerce-api-legacy (Tentativas: 0)
- [ ] Copiar `.claude/skills/refactor-arch/` para o projeto
- [ ] Rodar `/refactor-arch` — 3 fases executam (Node/Express detectado)
- [ ] Aplicação inicia e os 3 endpoints respondem (smoke test, log salvo)
- [ ] Relatório salvo em `reports/audit-project-2.md`
- [ ] Checklist de validação do projeto 2 preenchido
- [ ] Commit `refactor(ecommerce-api-legacy): aplica MVC via skill refactor-arch + relatório 2`

## Etapa 5 — Execução no Projeto 3: task-manager-api (Tentativas: 0)
- [ ] Copiar `.claude/skills/refactor-arch/` para o projeto
- [ ] Rodar `/refactor-arch` — Fase 1 detecta Python/Flask + domínio Task Manager
- [ ] Fase 2 identifica problemas no projeto parcialmente organizado
- [ ] Fase 3 melhora a estrutura sem quebrar; todos os endpoints respondem (smoke test, log salvo)
- [ ] Relatório salvo em `reports/audit-project-3.md`
- [ ] Checklist de validação do projeto 3 preenchido
- [ ] Commit `refactor(task-manager-api): aplica MVC via skill refactor-arch + relatório 3`

## Etapa 6 — README final (Tentativas: 0)
- [ ] Seção B "Construção da Skill"
- [ ] Seção C "Resultados" (findings por severidade, antes/depois, checklists, logs, observações por stack)
- [ ] Seção D "Como Executar"
- [ ] As 3 cópias da skill idênticas (`diff -r`)
- [ ] Commit `docs: README com construção da skill, resultados e como executar`

## Etapa 7 — Entrega (Tentativas: 0)
- [ ] `git status` limpo; `reports/audit-project-{1,2,3}.md` presentes
- [ ] `git push origin main` e conferência da árvore no GitHub
- [ ] Enviar URL do fork na plataforma (somente após autorização do usuário)

---

## Checklists de Validação por projeto

### Projeto 1 — code-smells-project
#### Fase 1 — Análise
- [x] Linguagem detectada corretamente
- [x] Framework detectado corretamente
- [x] Domínio da aplicação descrito corretamente
- [x] Número de arquivos analisados condiz com a realidade
#### Fase 2 — Auditoria
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados
- [x] Detecção de APIs deprecated incluída (se aplicável)
- [x] Skill pausa e pede confirmação antes da Fase 3
#### Fase 3 — Refatoração
- [x] Estrutura de diretórios segue padrão MVC
- [x] Configuração extraída para módulo de config (sem hardcoded)
- [x] Models criados para abstrair dados
- [x] Views/Routes separadas para visualização ou roteamento
- [x] Controllers concentram o fluxo da aplicação
- [x] Error handling centralizado
- [x] Entry point claro
- [x] Aplicação inicia sem erros
- [x] Endpoints originais respondem corretamente

### Projeto 2 — ecommerce-api-legacy
#### Fase 1 — Análise
- [ ] Linguagem detectada corretamente
- [ ] Framework detectado corretamente
- [ ] Domínio da aplicação descrito corretamente
- [ ] Número de arquivos analisados condiz com a realidade
#### Fase 2 — Auditoria
- [ ] Relatório segue o template definido nos arquivos de referência
- [ ] Cada finding tem arquivo e linhas exatos
- [ ] Findings ordenados por severidade (CRITICAL → LOW)
- [ ] Mínimo de 5 findings identificados
- [ ] Detecção de APIs deprecated incluída (se aplicável)
- [ ] Skill pausa e pede confirmação antes da Fase 3
#### Fase 3 — Refatoração
- [ ] Estrutura de diretórios segue padrão MVC
- [ ] Configuração extraída para módulo de config (sem hardcoded)
- [ ] Models criados para abstrair dados
- [ ] Views/Routes separadas para visualização ou roteamento
- [ ] Controllers concentram o fluxo da aplicação
- [ ] Error handling centralizado
- [ ] Entry point claro
- [x] Aplicação inicia sem erros
- [ ] Endpoints originais respondem corretamente

### Projeto 3 — task-manager-api
#### Fase 1 — Análise
- [ ] Linguagem detectada corretamente
- [ ] Framework detectado corretamente
- [ ] Domínio da aplicação descrito corretamente
- [ ] Número de arquivos analisados condiz com a realidade
#### Fase 2 — Auditoria
- [ ] Relatório segue o template definido nos arquivos de referência
- [ ] Cada finding tem arquivo e linhas exatos
- [ ] Findings ordenados por severidade (CRITICAL → LOW)
- [ ] Mínimo de 5 findings identificados
- [ ] Detecção de APIs deprecated incluída (se aplicável)
- [ ] Skill pausa e pede confirmação antes da Fase 3
#### Fase 3 — Refatoração
- [ ] Estrutura de diretórios segue padrão MVC
- [ ] Configuração extraída para módulo de config (sem hardcoded)
- [ ] Models criados para abstrair dados
- [ ] Views/Routes separadas para visualização ou roteamento
- [ ] Controllers concentram o fluxo da aplicação
- [ ] Error handling centralizado
- [ ] Entry point claro
- [x] Aplicação inicia sem erros
- [ ] Endpoints originais respondem corretamente

---

## Critérios de Aceite (3/3 projetos)
| Critério | P1 | P2 | P3 |
|---|---|---|---|
| Fase 1 detecta stack corretamente | [x] | [ ] | [ ] |
| Fase 2 encontra >= 5 findings | [x] | [ ] | [ ] |
| Fase 2 inclui pelo menos 1 CRITICAL ou HIGH | [x] | [ ] | [ ] |
| Fase 3 aplicação funciona após refatoração | [x] | [ ] | [ ] |
