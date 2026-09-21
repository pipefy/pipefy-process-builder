# Receitas GraphQL — leitura e escrita econômicas

Estas queries existem por um motivo medido: **o custo de uma operação no Pipefy não é o resultado
da tool, é o contexto inteiro reenviado a cada chamada** (~45–60 mil tokens de schemas do conector
por turn). Ler um pipe pelo padrão ingênuo (`get_pipe` + `get_phase_fields` por fase + condicionais
por fase) custa **25 chamadas**; a query abaixo faz o mesmo em **1**. Use estas receitas sempre que
puder.

> ## Antes de escrever qualquer mutation, leia isto
>
> As **queries de leitura** deste arquivo podem ser reusadas direto: elas são exercitadas em todo
> build e falham alto quando erram.
>
> **Mutation é outra história.** Um exemplo de mutation aqui — ou em qualquer lugar — **não é
> autoridade sobre o schema**. Nome de campo de input do Pipefy mistura `snake_case` e
> `camelCase` sem padrão, inclusive dentro do mesmo input, e um nome errado passa pela sua
> revisão sem chamar atenção. Portanto, **antes do primeiro uso de uma mutation num build**:
>
> 1. Introspecte o input dela (`introspect_mutation`) **e o tipo de item de cada lista** que ela
>    receba (`introspect_type`) — o erro mora justamente aí, um nível abaixo do input principal,
>    onde a introspecção do input não chega.
> 2. Confira nome **e cardinalidade** de cada campo: um campo que é `LIST` recusa valor simples.
> 3. Registre a forma confirmada no `changes.md` junto da decisão fechada.
>
> É **uma** chamada de leitura por mutation por build. Custa menos que um build que passa na
> validação estrutural e falha em execução — que foi o que já aconteceu: uma mutation escrita a
> partir de exemplo, com dois nomes de campo errados e uma cardinalidade errada, chegou a flow
> publicado sem ninguém notar.

> **Nunca** passe `include_parsed=True` no `execute_graphql`: ele devolve o payload duplicado
> (string `result` + dict `data`) e infla o contexto sem nenhum ganho.

---

## 1. Auditoria estrutural completa — 1 chamada

Traz pipe, preferências de segurança, formulário inicial (com o id da fase oculta que o abriga),
campo de título, webhooks, conexões com outros pipes, todas as fases com todos os campos (rótulo,
tipo, obrigatoriedade, opções, ordem) e as condicionais com regra e ações completas. É a leitura
que serve à conferência, ao diagnóstico e ao review. *(Query exercitada ao vivo em 2026-08-31,
incluindo os campos novos da v3.2.)*

```graphql
query AuditPipe($id: ID!) {
  pipe(id: $id) {
    id name uuid public
    startFormPhaseId
    title_field { id internal_id label }
    only_admin_can_remove_cards
    only_assignees_can_edit_cards
    expiration_time_by_unit
    expiration_unit
    countOnlyWeekDays
    labels { id name }
    parentsRelations { id name }
    childrenRelations { id name }
    webhooks { id name url actions }
    start_form_fields { id internal_id uuid label type required options }
    fieldConditions {
      id name
      condition { expressions_structure expressions { structure_id field_address operation value } }
      actions { actionId whenEvaluator phase { id name } phaseField { id internal_id label } }
    }
    phases {
      id name index done description
      next_phase_ids
      cards_can_be_moved_to_phases { id name }
      fields { id internal_id uuid label type required editable options description index }
    }
  }
}
```

Variáveis: `{"id": "<pipe_id>"}`.

**Pipe grande (dezenas de condicionais, centenas de campos): a resposta pode passar do limite de
retorno da tool e ser salva em arquivo.** Nesse caso rode duas variantes em vez de processar o
arquivo à mão: `AuditPipeCore` = a query acima **sem** o bloco `fieldConditions`; `AuditPipeConditions`
= `pipe(id:) { id fieldConditions { ...o mesmo bloco... } }`. Duas chamadas, zero parsing manual.

**O que a `AuditPipe` não vê e a porta A precisa ver:** flows iPaaS. Quando o pipe tiver iPaaS
habilitado, `get_ipaas_tools(pipe_id)` + `ap_list_flows` + `ap_list_runs` fazem parte da leitura
padrão (`diagnostico.md`). Webhooks são só o rastro; o flow é o objeto.

**O que ela já responde sozinha:** fases (nomes, ordem, done), campos por fase com uuid, tipo e
obrigatoriedade, opções de select, movimentos permitidos entre fases, defaults de segurança,
campo de título, conexões com outros pipes, webhooks (o rastro de integrações externas) e **as
condicionais com a regra completa** — expressões (campo, operação, valor) e ações (qual campo
esconde/mostra, em que fase, em qual ramo).

Três pontos desta query evitam diagnósticos errados que já aconteceram (tudo verificado ao vivo):

- **`startFormPhaseId` é o id da fase virtual do formulário inicial.** O Pipefy modela o start
  form como uma fase oculta que **nunca aparece em `phases`**. É nela que os campos da "Fase 0"
  do spec são criados, e é o `phase_id` que a criação de condicional espera. Não deduza esse id
  (já se adivinhou "id da primeira fase − 1") — ele está aqui.
- **Não leia ancoragem de condicional pelo aninhamento em fase.** `phases[].fieldConditions`
  volta vazio mesmo em pipe cheio de condicionais, e o atributo `phase` de toda condicional
  aponta para a fase Start form — é indexação da plataforma, não defeito. A ancoragem real está
  nas **ações**: `actions[].phaseField` diz o campo afetado, `actions[].phase` a fase, e
  `whenEvaluator` o ramo (if-true/if-false).
- **`title_field` mostra o campo de título atual** — a leitura par da mutation da seção 6.

**O que ela não traz** (some 2 chamadas, não 24):
- Automações → a query da **seção 5** (com a condição de disparo, que `get_automations` omite).
- Agentes de IA → `aiAgents` paginado (§8.4), só quando o spec previr agentes — `get_ai_agents`
  devolve uma página sem aviso.

Então uma auditoria completa custa **3 a 6 chamadas, paginadas** — mais a leitura iPaaS
(`get_ipaas_tools` + `ap_list_flows`) quando o pipe tiver flows. Se você se pegar chamando
`get_phase_fields` em loop, pare: você está pagando 25 turns por algo que custa 1.

---

## 2. Criar campos em lote — aliases numa mutation só

Criar 18 campos em 18 chamadas custa 18 turns. Com alias, custa 1 (ou 3–4 se você quebrar por
fase, o que também ajuda a isolar erro). Shape validado:

```graphql
mutation CriarCampos {
  c1: createPhaseField(input: {
    phase_id: "<phase_id>", label: "Fornecedor", type: "short_text", required: true
  }) { phase_field { id internal_id label } }

  c2: createPhaseField(input: {
    phase_id: "<phase_id>", label: "Valor total", type: "currency", required: true
  }) { phase_field { id internal_id label } }

  c3: createPhaseField(input: {
    phase_id: "<phase_id>", label: "Categoria", type: "select",
    options: ["Serviço", "Material", "Software"]
  }) { phase_field { id internal_id label } }
}
```

`CreatePhaseFieldInput` — obrigatórios: `label`, `phase_id`, `type`. Opcionais úteis: `options`
(lista de string), `required`, `description`, `help`, `editable`, `index`, `minimal_view`,
`custom_validation`, `sync_with_card`, e os de conector (`connectedRepoId`, `canConnectExisting`,
`canConnectMultiples`, `canCreateNewConnected`, `allChildrenMustBeDoneToFinishParent`,
`allChildrenMustBeDoneToMoveParent`, `childMustExistToFinishParent`).

Regra de rótulo continua valendo (ver `nomenclature.md` e `02-builder.md`): crie com rótulo
limpo, sem `/`, `.` ou emoji, para o slug nascer limpo.

## 3. Criar fases em lote

```graphql
mutation CriarFases {
  f1: createPhase(input: { pipe_id: "<pipe_id>", name: "Triagem", index: 1 }) { phase { id name } }
  f2: createPhase(input: { pipe_id: "<pipe_id>", name: "Aprovação", index: 2 }) { phase { id name } }
  f3: createPhase(input: { pipe_id: "<pipe_id>", name: "Concluído", done: true, index: 3 }) { phase { id name } }
}
```

`CreatePhaseInput`: `pipe_id`, `name`, `index`, `done`, `description`, `lateness_time`,
`can_receive_card_directly_from_draft`, `only_admin_can_move_to_previous`.

> **`create_pipe` ignora o parâmetro `phases` silenciosamente** — o pipe nasce com as 3 fases
> default em português, sem nenhum aviso. Não passe fases na criação: crie-as aqui em lote e
> remova as default na sequência (o clean slate do Builder).

**Limite de lote:** cerca de **30 campos por chamada**. Acima disso a chamada falha. Quebre em
blocos de ~20 para ter margem — e quebrar por fase já ajuda a isolar erro.

**Cuidado com lote em mutations:** se uma alias falhar, as outras podem ter sido aplicadas.
Antes de repetir um lote que deu erro, releia com a query da seção 1 e recrie **apenas o que
faltou** — nunca reenvie o lote inteiro às cegas (duplicaria campos).

> ⚠️ **Erro pode ser falso-negativo.** Já houve caso de resposta `success: false` com mensagem
> vazia enquanto a operação **tinha sido aplicada** — e o retry duplicou 18 cards de um cliente.
> Regra dura: **depois de qualquer erro ou timeout numa escrita, releia o estado real antes de
> repetir.** Nunca repita às cegas.

Automações e condicionais **continuam pelas tools dedicadas** (`create_automation`,
`create_field_condition`): elas têm normalização de payload e validações que evitam os
travamentos descritos em `connector-rules.md`. Não vale a pena arriscar lote ali.

---

## 4. Validar um documento GraphQL sem gastar payload

Para conferir se uma query nova é válida antes de rodá-la de verdade, execute-a com um id
inexistente (`{"id": "1"}`). O GraphQL valida o documento **antes** de executar: campo inválido
volta como erro nomeado ("Field 'x' doesn't exist on type 'Y'") sem trazer dado nenhum, e um erro
de execução ("Permission denied") significa que o documento está correto. Custa quase nada
comparado a rodar contra um pipe real e descobrir o erro depois.

---

## 5. Ler automações **com a condição de disparo**

`get_automations` devolve gatilho e ação mas **omite a condição** — o "se X então". Isso já fez um
revisor concluir que uma automação estava sem condição e **reprovar um build inteiro** por um dado
que existia, mas estava invisível. Sempre que precisar auditar ou revisar automações, use esta
query em vez da tool:

```graphql
query AutomacoesComCondicao($orgId: ID!, $pipeId: ID!, $after: String) {
  automations(organizationId: $orgId, repoId: $pipeId, first: 50, after: $after) {
    pageInfo { hasNextPage endCursor }
    edges { node {
      id name active event_id action_id disabledReason
      condition {
        id
        expressions_structure
        expressions { structure_id field_address operation value }
      }
    } }
  }
}
```

Variáveis: `{"orgId": "<organization_id>", "pipeId": "<pipe_id>"}`. O `organization_id` é
obrigatório. Note o `active` e o `disabledReason`: automação criada com `active=false` para teste e
esquecida desativada é defeito comum.

**Pagina até `hasNextPage: false`.** A conexão corta em 50 mesmo com `first: 400`; um pipe de 178
automações mostrou 50, e uma conferência reprovou um build inteiro por "automação inexistente".
Declare no relatório "lidas N de N". Para checar automações específicas sem paginar, use o
verificador da §8.2. Nota: a issue #612 do `ai-toolkit` (condição em `get_automations`) foi fechada em
17/09/2026 — se a tool passar a devolver `condition`, ela serve; a query continua valendo como fonte.

## 6. Configurar segurança do pipe e campo de título

A tool `update_pipe` aceita só nome, ícone e cor — mas **a API aceita mais**. Os defaults de
segurança das best practices e o campo de título **não são pendência manual**: dá para configurar
aqui.

```graphql
mutation ConfigurarPipe($id: ID!) {
  updatePipe(input: {
    id: $id
    public: false
    public_form: false
    only_assignees_can_edit_cards: true
    only_admin_can_remove_cards: true
    title_field_id: "<SLUG do campo — o id textual, ex.: nome>"
  }) { pipe { id public only_assignees_can_edit_cards only_admin_can_remove_cards title_field { id } } }
}
```

`title_field_id` resolve o efeito de "título do card trocado sozinho": por default o Pipefy usa o
primeiro campo como título, então aponte explicitamente qual campo deve ser o título.

> ⚠️ **`title_field_id` aceita somente o slug do campo** (o `id` textual, ex.: `nome`), **nunca o
> `internal_id` numérico** — com internal_id a mutation falha com `Field not found with id: ...`.
> É uma inconsistência real do schema (o resto endereça campo por `internal_id`), tropeçada em
> três builds independentes e verificada ao vivo. O campo de título atual é legível por
> `title_field` na query da seção 1.

**O que realmente não existe:** `description` não está em `UpdatePipeInput` — a descrição do pipe
é a única parte que continua pendência manual na UI.

## 7. Atualizar valores de campos de card em lote

Para correção em massa de dados (o caso de centenas de valores), `update_card_field` custa uma
chamada por campo. A API tem `updateFieldsValues`, que atualiza **vários campos de um card numa
chamada** — e com alias você cobre **vários cards no mesmo documento**:

```graphql
mutation CorrigirCards {
  c1: updateFieldsValues(input: {
    nodeId: "<card_id_1>"
    values: [
      { fieldId: "<internal_id>", value: "novo valor" },
      { fieldId: "<internal_id>", value: "outro valor" }
    ]
  }) { success userErrors { field message } }

  c2: updateFieldsValues(input: {
    nodeId: "<card_id_2>"
    values: [{ fieldId: "<internal_id>", value: "novo valor" }]
  }) { success userErrors { field message } }
}
```

Peça `userErrors` por alias: é assim que você sabe **qual item falhou** em vez de descobrir que o
lote inteiro "deu erro". Vale a mesma regra da seção 2: erro num alias não invalida os outros —
releia antes de repetir.

> Se a forma de `values` recusar, valide com a técnica da seção 4 e introspecte
> `__type(name: "UpdateFieldsValuesInput")` uma única vez.

> **Anexo tem formato diferente em cada mutation:** aqui em `updateFieldsValues`, o valor de um
> campo de anexo é **string simples** com o `storage_path`; em `createCard`,
> `fields_attributes[].field_value` é **LIST** (`["valor"]`) para qualquer tipo de campo, anexo
> incluído — e errar esse formato devolve a mensagem enganosa "campo obrigatório não preenchido".
> O fluxo completo de upload está em `connector-rules.md`, seção 4.8.

## 8. Receitas da rodada 3.03

### 8.1 updatePhaseField por uuid
Endereçar por slug já alterou campos de **outro pipe** (slug não é único). Use o `uuid` do campo
lido na `AuditPipe` do alvo e confira o `internal_id` devolvido:

```graphql
mutation AtualizarCampo($uuid: ID!, $label: String!, $required: Boolean) {
  updatePhaseField(input: { uuid: $uuid, id: $uuid, label: $label, required: $required }) {
    phase_field { id internal_id uuid label required }
  }
}
```
`label` é obrigatório — envie o rótulo **atual** (valor diferente renomeia). Se `internal_id` da
resposta ≠ o esperado: pare, reverta, avise. *(Input validado por introspecção em 2026-09-21:
`UpdatePhaseFieldInput` tem `uuid: ID`, `id: ID!`, `label: String!` — a mutation não foi executada,
só o shape, conforme a regra da abertura deste arquivo. Tabela completa de identificador por
mutation: `connector-rules.md`, §4.3.)*

### 8.2 Verificador de automações por id (aliases)
Imune ao corte de 50. Um documento confere até ~15 automações:

```graphql
query VerificarAutomacoes {
  a1: automation(id: "<id1>") { id name active event_id action_id condition { expressions_structure expressions { field_address operation value } } }
  a2: automation(id: "<id2>") { id name active event_id action_id condition { expressions_structure expressions { field_address operation value } } }
}
```

### 8.3 Automações paginadas
A query da seção 5 com `$after` = `endCursor` da página anterior, até `hasNextPage: false`.

### 8.4 Agentes de IA paginados
`get_ai_agents` devolve uma página (10 de 22 num pipe real) sem sinal. Leia por GraphQL:

```graphql
query Agentes($repoUuid: ID!, $after: String) {
  aiAgents(repoUuid: $repoUuid, first: 30, after: $after) {
    pageInfo { hasNextPage endCursor }
    edges { node { uuid name disabledAt lastExecution needReview } }
  }
}
```
`AiAgent` **não tem `id`** — identifica-se por `uuid`; `disabledAt: null` = ativo. `repoUuid` é o
`uuid` do pipe (na `AuditPipe`). Snapshot de agentes só é válido com `hasNextPage: false`.
*(Validado ao vivo em 2026-09-21 no sandbox 301781351.)*

### 8.5 Logs de execução (automationLogsByRepo)
Para contar execuções (a métrica `executionMetrics` pode vir zerada):

```graphql
query Logs($repoId: ID!, $after: String) {
  automationLogsByRepo(repoId: $repoId, first: 50, after: $after) {
    pageInfo { hasNextPage endCursor }
    edges { node { uuid automationId automationName cardId cardTitle datetime status } }
  }
}
```
`AutomationLog` **não tem `id`** (é `uuid`); `cardId` pode vir nulo. `status: success` =
**avaliada**, não executada (`connector-rules.md`, §4.5). *(Validado ao vivo em 2026-09-21.)*

### 8.6 phases_history — assentamento da cascata
Antes de julgar resultado de teste (cascata leva 2–3 min):

```graphql
query Assentou($id: ID!) {
  card(id: $id) { id late expired
    phases_history { phase { id name } firstTimeIn lastTimeOut duration } }
}
```
A fase atual é a entrada com `lastTimeOut: null`. Releia a cada 60 s até duas leituras iguais.

### 8.7 Registros de tabela paginados
`table_records` ignora `first` acima de 50 e não devolve total:

```graphql
query Registros($tableId: ID!, $after: String) {
  table_records(table_id: $tableId, first: 50, after: $after) {
    pageInfo { hasNextPage endCursor }
    edges { node { id title record_fields { name value } } }
  }
}
```
Releitura completa após cada lote de escrita; compare **estrito** (caractere a caractere) além do
normalizado. *(Shape validado só como documento em 2026-09-21 — id inexistente devolveu erro
genérico, não dado real; confirme com tabela real na primeira utilização.)*
