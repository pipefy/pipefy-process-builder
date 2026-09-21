# Pipefy Process Builder

Skill do Claude Code para consultores de Professional Services da Pipefy. Conduz, numa única
conversa, o diagnóstico, a criação, a evolução, o cálculo de ROI ou a montagem de um deck de
apresentação para um processo (pipe) no Pipefy do cliente — do pedido inicial até a entrega, com
aprovação explícita antes de qualquer escrita.

## Pré-requisitos

- **Claude Code** com acesso ao **connector MCP do Pipefy** habilitado e autorizado na organização
  do cliente.
- Permissão de leitura (mínima) para os fluxos de diagnóstico; permissão de escrita para criar ou
  alterar pipes.
- Se o escopo envolver **iPaaS**, o mesmo connector precisa expor o catálogo iPaaS do pipe alvo
  (veja `references/ipaas.md`).

## Instalação

O pacote é publicado no npm como
[`@pipefy/pipefy-process-builder`](https://www.npmjs.com/package/@pipefy/pipefy-process-builder). Um
script de `postinstall` já coloca `SKILL.md`, `references/` e `perks/` no lugar certo — não precisa
copiar nada na mão:

```bash
# no projeto (instala em .claude/skills/pipefy-process-builder/)
npm install @pipefy/pipefy-process-builder

# globalmente (instala em ~/.claude/skills/pipefy-process-builder/, disponível em qualquer projeto)
npm install -g @pipefy/pipefy-process-builder
```

Resultado esperado em qualquer um dos dois casos:

```
<diretório de skills>/pipefy-process-builder/
├── SKILL.md
├── references/
│   ├── 01-planner.md
│   ├── 02-builder.md
│   └── ...
└── perks/
    └── create-email-template/
```

**Se você (ou sua política de CI/segurança) instalar com `--ignore-scripts`**, o `postinstall` não
roda e os arquivos ficam só dentro de `node_modules/@pipefy/pipefy-process-builder/` — nesse caso,
copie `SKILL.md`, `references/` e `perks/` de lá para o diretório de skills acima manualmente (ou
rode `node node_modules/@pipefy/pipefy-process-builder/scripts/install-skill.js` depois, que faz a
mesma cópia).

---

`perks/create-email-template/` é um wrapper MCP local **opcional**: sem ele, criação de template de
e-mail cai automaticamente como pendência manual na UI (veja `perks/create-email-template/README.md`
para instalar).

Depois de instalada, a skill é carregada automaticamente pelo Claude Code quando o pedido do
consultor casar com sua descrição (diagnosticar, criar ou evoluir um processo no Pipefy).

## Como usar

Basta pedir em português, em uma conversa normal com o Claude Code. Alguns exemplos:

- *"Diagnostica o pipe de Compras desse cliente"* → abre a **porta A** (diagnóstico, somente leitura).
- *"Quero montar um processo de onboarding do zero"* → abre a **porta B** (criação, com discovery e
  aprovação de spec antes de construir).
- *"Preciso ajustar o pipe de Reembolso que já existe"* → abre a **porta C** (evolução, com deltas).
- *"Quanto esse processo já economizou?"* → abre a **porta D** (ROI, a partir de um diagnóstico).
- *"Monta um deck com esse diagnóstico para eu apresentar"* → abre a **porta E** (deck em PDF).

A skill conduz a conversa inteira — discovery, aprovação, construção via MCP e conferência
estrutural — e cria uma pasta `builds/<cliente>-<dominio>-<AAAA-MM-DD>/` no diretório onde o Claude
Code está rodando, **não** dentro deste repositório. É ali que ficam os artefatos da sessão
(`spec.md`, `changes.md`, `diagnostico.md`, `conferencia.md` etc.), o que também é o que permite
retomar um trabalho interrompido: aponte a pasta e a skill continua da etapa pendente.

Nenhuma escrita no Pipefy acontece sem aprovação explícita do consultor sobre o spec.

## Estrutura do repositório

| Arquivo | Papel |
|---|---|
| `SKILL.md` | Orquestrador — portas, disciplina de custo, regras globais |
| `references/01-planner.md` | Discovery e definição do `spec.md` (porta B/C) |
| `references/02-builder.md` | Construção via MCP a partir do spec aprovado |
| `references/03-conferencia.md` | Playbook de conferência estrutural (subagente somente leitura) |
| `references/diagnostico.md` | Motor de diagnóstico (porta A) |
| `references/golden_standard_schema.md` | Padrão de referência por domínio |
| `references/decision_catalog.md` | Catálogo de variações/decisões conhecidas |
| `references/connector-rules.md` | Limites e armadilhas conhecidas do connector Pipefy |
| `references/graphql-recipes.md` | Receitas de leitura/escrita em lote via GraphQL |
| `references/handoff-schemas.md` | Contrato de cada arquivo gerado durante o uso |
| `references/ipaas.md` | Fluxo para integrações iPaaS no escopo |
| `references/roi.md` | Cálculo de ROI do processo (porta D) |
| `references/deck.md`, `references/deck-template.html` | Deck de apresentação em PDF (porta E) |
| `references/teste-funcional.md`, `references/review-completo.md` | Etapas opcionais, sob pedido do consultor |
| `references/discovery_questions.md`, `references/modeling_best_practices.md`, `references/nomenclature.md` | Apoio ao discovery e às boas práticas de modelagem |
| `perks/create-email-template/` | Wrapper MCP local opcional para criar template de e-mail nativamente |
