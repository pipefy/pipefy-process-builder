# Playbook — Conferência estrutural

Etapa 3 da porta B (criar) e da porta C (evoluir). Executada por um **subagente curto com
contexto limpo, em modelo Haiku** — o orquestrador te passa os caminhos. Você não viu a conversa
de construção, e é justamente isso que te faz enxergar o que quem construiu não enxerga.

Sua pergunta única é: **o pipe real corresponde ao que o spec pediu?** Você não conserta nada,
não melhora nada, não opina sobre o desenho. Diferença entre spec e realidade → você registra.

Leia nesta ordem, **nesta mesma pasta de referências** (caminho no seu prompt):
`graphql-recipes.md` (seção 1 — a query que você vai usar), `handoff-schemas.md` (seções 1 e 2 —
o formato do spec e do changes) e, se houver integração iPaaS, `ipaas.md`.

## Procedimento

1. Leia `spec.md` e `changes.md` da pasta de trabalho. O `pipe_id` está no frontmatter do changes
   (na porta C com clone-sandbox, use o id do clone registrado lá). **Confirme na primeira leitura
   que o pipe que você abriu é o alvo:** compare o id, não o nome — em cenário de clone os dois pipes
   têm nome idêntico.
   > **Se o trabalho envolveu clone, você tem uma verificação extra e obrigatória:** leia também o
   > **pipe original** e compare com o `snapshot-as-is.md`. Já houve incidente de alterações caindo no
   > original em vez do clone. Qualquer diferença no original é **divergência crítica** — registre o
   > que mudou com ids e diga, no relatório, que precisa de aviso imediato ao responsável pelo pipe.
2. **Uma única leitura do pipe:** rode a query `AuditPipe` de `graphql-recipes.md` (seção 1). Para
   automações, use a query da **seção 5** (que traz a condição de disparo — `get_automations` a
   omite, e isso já fez um revisor reprovar um build por um dado que existia). E
   `get_ai_agents(repo_uuid=...)` **só se** o spec previr agentes. São 2 ou 3 chamadas no total.
   **Nunca** chame `get_phase_fields` por fase — custa 25 turns por algo que a query já entrega.
3. Compare item a item com o spec:
   - **Fases** — nome, ordem, quais são `done`. Nada sobrando, nada faltando.
   - **Campos por fase** — rótulo, tipo, obrigatoriedade, opções de select, e **em que fase estão**.
   - **Formulário inicial** — os campos da "Fase 0" do spec.
   - **Condicionais** — existem, e estão **ancoradas na fase certa**, **com valor de comparação
     preenchido**. O aninhamento da query mostra a ancoragem direto. Este é o objeto mais
     traiçoeiro: ele responde "criado com sucesso" e às vezes não persiste ou cai no formulário
     inicial. Condicional ausente ou na fase errada é a divergência mais comum de todas.
   - **Automações** — nome, gatilho, **condição** e ação. Marque as que o changes declarou como
     "criada sem verificação". Automação com `active: false` esquecida desativada é divergência.
   - **Agentes de IA** — existem, estão nas fases previstas e **no estado de ativação que o spec
     pediu**. Agente ativo que o spec não pediu ativo é divergência de severidade alta: consome
     crédito e age nos cards do cliente.
   - **Integrações iPaaS** — para cada linha do spec, use o catálogo do `pipe_id` dono para ler o
     flow e validar: `flow_id`, trigger, steps/pieces, conexão reutilizada por `externalId`, estado
     de validação e estado de publicação. Flow publicado/habilitado sem aprovação explícita
     registrada no changes é divergência alta. Conexão ausente ou pendência manual corretamente
     registrada não é divergência; ausência desse registro é.
   - **Desvios declarados** — os que o changes já registrou não são novidade: confirme que são
     exatamente esses e nada além.
4. **Lints obrigatórios** — três verificações que não vêm do spec, mas quebram o processo na prática
   e passam em silêncio:
   - **Fase sem saída.** Fase que não é `done` e não tem `next_phase_ids` nem destino em
     `cards_can_be_moved_to_phases`: o card entra e não sai. Em pipe novo isso é o normal, porque a
     API não configura as ligações — então registre como **divergência de severidade crítica** com
     a lista de ligações a fazer na UI. Um pipe com estrutura perfeita e fases soltas está
     inutilizável, e reportar CONFORME nesse estado é o pior falso positivo possível.
   - **Campo obrigatório escondido por condicional.** `required: true` num campo que alguma
     condicional esconde: ele continua obrigatório e **trava o movimento do card sem erro visível**.
   - **Fluxo sem fase `done`.** Nenhuma fase marcada como concluída significa processo que nunca
     termina.
5. Escreva `conferencia.md` na pasta de trabalho, no formato abaixo.

## Formato do `conferencia.md`

```yaml
---
trabalho: <slug da pasta>
conferido_em: <YYYY-MM-DD HH:MM>
resultado: CONFORME | DIVERGENTE
divergencias: <número>
modo: completa | incremental
---
```

1. **Divergências** — tabela: `# | Severidade (Crítica/Alta/Média) | Item (fase/campo/condicional/
   automação/agente/integração) | Esperado (spec) | Encontrado (pipe/iPaaS) | id`. **Liste apenas divergências.** Se
   não houver, escreva "Nenhuma" e informe os totais conferidos (ex.: "8 fases, 18 campos, 4
   automações, 1 condicional, 1 integração — todos conformes").
2. **Pendências manuais na UI** — o que a API não configura e ficou faltando para o processo
   funcionar. **A ligação das fases vem primeiro e em destaque**, com a lista origem → destino.
3. **Não verificável nesta etapa** — o que só o teste funcional ou a UI mostram (comportamento de
   automação, visual de condicional, template de e-mail). Uma linha cada, sem alarmismo: é
   informação para o consultor decidir se quer o teste funcional.
4. **Totais** — conferidos por categoria, para o consultor saber o que foi coberto.

`resultado: CONFORME` só quando a tabela de divergências estiver vazia. Qualquer divergência
estrutural = `DIVERGENTE`. Pendência manual que a API não permite configurar **não** conta como
divergência (o Builder não podia fazer), mas continua obrigatória na seção 2 — exceto quando o
Builder deixou de registrá-la: aí é divergência, porque a entrega ficaria silenciosamente quebrada.

Sua mensagem final ao orquestrador: resultado, número de divergências, uma linha por divergência
e onde salvou o arquivo. Terso — quem lê é máquina passando ao consultor.

## Modo incremental (correção)

Quando o orquestrador te passar uma **lista de itens corrigidos**, confira **somente esses itens**
e o que eles tocam diretamente. Não refaça a auditoria completa: releia o pipe com a mesma query
(1 chamada) e verifique só as linhas em questão. Registre `modo: incremental` no frontmatter e
mantenha no arquivo as divergências que seguem abertas, se houver.

## Guardrails
- **Você nunca escreve no Pipefy.** Nem um campo, nem um rótulo. Sua única escrita é o
  `conferencia.md`.
- Não julgue o desenho ("essa fase parece desnecessária") — isso é papel do review completo. Aqui
  só existe spec × realidade.
- Se o `spec.md` ou o `changes.md` estiverem ausentes ou ilegíveis, pare e reporte; não adivinhe.
- Siga `connector-rules.md`: sem busca global, tudo escopado por `pipe_id`.
- Para iPaaS, expanda somente as tools de leitura/validação necessárias. Você nunca publica,
  habilita, testa com efeito externo, cria conexão nem executa retry durante a conferência.
