# Receitas GraphQL — leitura e escrita econômicas

Estas queries existem por um motivo medido: **o custo de uma operação no Pipefy não é o resultado
da tool, é o contexto inteiro reenviado a cada chamada** (~45–60 mil tokens de schemas do conector
por turn). Ler um pipe pelo padrão ingênuo (`get_pipe` + `get_phase_fields` por fase + condicionais
por fase) custa **25 chamadas**; a query abaixo faz o mesmo em **1**. Use estas receitas sempre que
puder — e nunca introspecte o schema em runtime: as formas abaixo já foram validadas contra a API.

> **Nunca** passe `include_parsed=True` no `execute_graphql`: ele devolve o payload duplicado
> (string `result` + dict `data`) e infla o contexto sem nenhum ganho.

---

## 1. Auditoria estrutural completa — 1 chamada

Traz pipe, preferências de segurança, formulário inicial, todas as fases com todos os campos
(rótulo, tipo, obrigatoriedade, opções, ordem) e as condicionais ancoradas em cada fase. É a
leitura que serve à conferência, ao diagnóstico e ao review.

```graphql
query AuditPipe($id: ID!) {
  pipe(id: $id) {
    id name uuid public
    only_admin_can_remove_cards
    only_assignees_can_edit_cards
    expiration_time_by_unit
    expiration_unit
    countOnlyWeekDays
    labels { id name }
    start_form_fields { id internal_id label type required options }
    startFormFieldConditions { id name }
    phases {
      id name index done description
      next_phase_ids
      cards_can_be_moved_to_phases { id name }
      fields { id internal_id label type required editable options description index }
      fieldConditions { id name }
    }
  }
}
```

Variáveis: `{"id": "<pipe_id>"}`.

**O que ela já responde sozinha:** fases (nomes, ordem, done), campos por fase com tipo e
obrigatoriedade, opções de select, condicionais **e em que fase cada uma está ancorada** (o
aninhamento revela condicional na fase errada — o erro mais comum), movimentos permitidos entre
fases, e os defaults de segurança do pipe.

**O que ela não traz** (some 2 chamadas, não 24):
- Automações → `get_automations(pipe_id=...)`.
- Agentes de IA → `get_ai_agents(repo_uuid=...)` (só quando o spec previr agentes).
- Detalhe da regra de uma condicional → `get_field_condition(<id>)`, e **só** para a condicional
  que estiver sob suspeita, nunca para todas.

Então uma auditoria completa custa **2 a 3 chamadas**. Se você se pegar chamando
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
query AutomacoesComCondicao($orgId: ID!, $pipeId: ID!) {
  automations(organizationId: $orgId, repoId: $pipeId) {
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
    title_field_id: "<internal_id do campo que deve virar o título>"
  }) { pipe { id public only_assignees_can_edit_cards only_admin_can_remove_cards } }
}
```

`title_field_id` resolve o efeito de "título do card trocado sozinho": por default o Pipefy usa o
primeiro campo como título, então aponte explicitamente qual campo deve ser o título.

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
