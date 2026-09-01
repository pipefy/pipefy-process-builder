# Feedback consolidado para a engenharia do MCP Pipefy — agosto/2026

Consolidação das sugestões de engenharia extraídas de **nove relatórios de campo** de builds e
diagnósticos reais feitos com o `pipefy-process-builder` entre 20 e 31 de agosto de 2026:

| Fonte | Contexto |
|---|---|
| Onboarding PJ/PF (307240944) | Melhorias de conformidade + correção de automação órfã |
| Siniestros Chile (307319484 → 307320020) | Recriação de pipe completo com tradução PT→ES |
| Bemol CGI Garantias (307316105) | Pipe satélite com campos conector |
| AON Endoso (307322813) | Build do zero com agentes de IA e cards de demonstração |
| Ecom Energia | Agentes de IA (arquitetura automação × aba de Agentes) |
| POC de compras (porta C) | Evolução de pipe existente |
| Agentes com MCP tools (Slack/Docs) | Tentativa de criação via API |
| Firmas e Poderes (307240944) | Edição de agente + flow iPaaS |
| KYC Sócios (307279407) | Diagnóstico de flow iPaaS em produção |

Duplicatas foram fundidas; cada item traz a evidência. Os itens marcados **[validado ao vivo]**
foram reproduzidos em 2026-08-31 contra o pipe de testes 301781351 durante a preparação da v3.2 da
skill. Nota: a skill já **documenta contornos** para quase tudo aqui (v3.2) — este documento é a
lista do que só a engenharia resolve na raiz.

---

## 1. Agentes de IA (o cluster com mais incidentes: 6 relatórios)

1. **`update_ai_agent` deveria suportar patch parcial por behavior** (por `id`), em vez de
   replace-all do array. Hoje, enviar um subconjunto de `behaviors` apaga os demais **sem aviso** —
   apagou Compliance AI e Finance AI de um agente em produção quando só o Legal AI deveria mudar.
   *(Firmas e Poderes)*
2. **Erros estruturados em `create_ai_agent`/`update_ai_agent`.** "Houve um problema ao salvar o
   agente" não diz a causa. Causas reais descobertas por eliminação: `id`/`referenceId` reenviados
   nos behaviors/actions (o backend não os aceita de volta) e `value: ""` explícito em
   `fieldsAttributes`. Um erro como "campo `behaviors[].id` não é aceito — omita para gerar novo"
   economizaria horas por build. *(Firmas e Poderes, AON)*
3. **Expor o limite de 10.000 caracteres por instrução** no schema/description da tool, e
   idealmente validar client-side antes do POST. Hoje só se descobre no erro, depois de montar o
   payload inteiro. *(Firmas e Poderes)*
4. **Consertar ou aposentar `validate_ai_agent_behaviors`.** Ela valida contra `BehaviorInput`, um
   tipo que **não existe** no schema real (a mutation usa `AutomationInput`) — "válido" na tool não
   garante criação. Ou valida contra a cadeia real (`AutomationInput` + `AiBehaviorParamsInput` +
   `AiBehaviorActionAttributesInput` + `AiBehaviorMetadataInput`), ou marca-se como não confiável.
   *(AON)*
5. **Prevenir criação parcial de agente.** A API gera o id do agente mesmo quando a configuração
   das capabilities falha, deixando "agente fantasma" no banco. Sugestões: dry-run no payload antes
   da execução real, ou rollback automático quando a criação for parcial. *(Feedback AI Builder /
   teste com pipe clonado)*
6. **`requires_confirmation` para `toggle_ai_agent_status(active=false)`** e para qualquer mutação
   que desative agente como efeito colateral — mesmo padrão que `delete_phase`/`delete_card` já
   têm. Um subagente de conferência (read-only por contrato) desativou os 2 agentes de um build sem
   nenhum sinal. "Agente ativo/inativo sem o cliente saber" é risco conhecido; a proteção deveria
   ser simétrica. *(AON)*
7. **Emitir o `referenceId` da action na resposta da própria mutation de criação** — hoje ele só
   existe após o save e exige releitura do agente para ser descoberto (a plataforma insere a linha
   `%{action:...}` sozinha, o que é bom, mas não é documentado). *(Siniestros)*
8. **Nomes de parâmetro próximos para conceitos diferentes:** `get_ai_agents(repo_uuid)` ×
   `get_ai_agent(uuid do agente)` — sem exemplo no describe, é troca fácil. *(AON)*
9. **Suportar `actionType: "mcp_tool"` na criação via API.** O tipo existe no produto (agentes
   criados pela UI o usam), mas `create_ai_agent` só aceita 6 tipos e não há campo para amarrar a
   ação ao servidor MCP conectado ao pipe. Hoje qualquer agente que use Slack/Google Docs etc. é
   inconstruível por API. *(Agentes com MCP tools)*

## 2. Automações

10. **Alinhar o shape das tools dedicadas com o schema real** (`create_automation`,
    `update_automation`): a tool pede `trigger_id` onde o schema fala `event_id`; o gatilho de
    campo só entra por `extra_input.event_params.triggerFieldIds`; `strategy` é enum
    (`ROUND_ROBIN`/`RANDOM`). Três camadas de tentativa e erro para configurar um único gatilho.
    Ou alinhar, ou documentar o mapeamento tool-param → GraphQL-field no description. *(AON,
    Onboarding)*
11. **`create_automation` deveria validar a combinação evento×ação** e devolver, no erro, a lista
    de eventos compatíveis com a ação escolhida. `move_card`/`move_single_card` ×
    `field_updated` não existe; `distribute_assignments` × `card_created` não existe — e isso só se
    descobre chamando `get_automation_events`/`get_automation_actions` à parte. *(AON)*
12. **Expor o schema de escrita de `event_params`.** Chaves que `get_automation` retorna não são
    aceitas de volta no `update_automation` (ex.: `phase` → "Field is not defined on
    AutomationEventParamsInput"). Mesmo padrão do problema dos `id`s de agente. *(Onboarding)*
13. **`get_automation_topology(pipe_id)`**: automação → fase-gatilho (resolvida de
    `triggerFieldIds`) → fase-destino numa chamada. Hoje isso exige `get_automation` individual
    (12 chamadas num caso real) + cruzamento manual com a árvore de campos. *(Onboarding)*
14. **Expor a configuração real de `distribute_assignments` na leitura** — todos os campos
    relevantes vêm `null`, inclusive no pipe original, impossibilitando auditoria e réplica fiel.
    *(Siniestros)*
15. **Relatar por alias qual item de um lote falhou.** Numa mutation com 14 aliases, 5 falharam
    silenciosamente sem indicação de quais — só comparação antes/depois revelou. *(Siniestros)*

## 3. Campos, fases e pipe

16. **`create_pipe`: aplicar ou rejeitar explicitamente o parâmetro `phases`.** Hoje é aceito na
    assinatura e silenciosamente ignorado (o pipe nasce com as 3 fases default). *(AON)*
17. **Padronizar o identificador aceito entre mutations — ou errar com mensagem que diga o formato
    esperado.** Casos confirmados: `updatePipe.title_field_id` só aceita **slug**
    **[validado ao vivo: internal_id → "Field not found"]**; `delete_phase_field` exige
    **`pipe_uuid` + slug** (pipe_id numérico → PERMISSION_DENIED; internal_id → RESOURCE_NOT_FOUND)
    **[validado ao vivo]**; `updateFieldsValues` usa `internal_id`. Três formatos diferentes, erros
    genéricos. *(Siniestros, Bemol, AON)*
18. **Expor a fase oculta "Start form" de forma explícita** em `get_pipe`/queries de pipe — ex.:
    incluí-la em `phases` com flag `is_start_form: true`, ou documentar `startFormPhaseId` com
    destaque. Hoje nada relaciona o id solto à lista de fases, e o custo é alto: um build criou os
    13 campos do formulário na primeira fase visível e entregou o start form vazio — defeito que
    passa por **toda** verificação via API e só aparece na UI. **[comportamento validado ao vivo:
    `startFormPhaseId` retorna fase ausente de `pipe.phases`]** *(AON, Siniestros)*
19. **Health-check de campo `connector` pós-criação.** Campo criado via `createPhaseField` com
    `type: "connector"` pode nascer quebrado na UI ("We're sorry, something went wrong" no lugar do
    seletor) enquanto a API o retorna como saudável — não há nenhum sinal legível. Expor um
    booleano de sanidade (ex.: `connector_valid`) ou validar o `connectedRepoId` resolvido antes de
    reportar sucesso. *(Bemol)*
20. **Campo `statement` criado via API não renderiza na UI** (a API confirma criação e leitura; a
    UI não mostra — relatado em start form). Confirmar se é bug de plataforma ou específico da via
    API; enquanto isso, quem pede "conteúdo dinâmico" deve usar `dynamic_content`
    **[validado ao vivo: `dynamic_content` é criável via API]**. *(Relatório campo dinâmico +
    gravação)*
21. **`create_card`: erro de tipo claro quando `field_value` chega escalar.** O tipo é LIST; o
    valor escalar hoje devolve "campo obrigatório não preenchido" — mensagem de negócio que aponta
    para o lugar errado (três hipóteses falsas investigadas antes da introspecção). *(AON)*
22. **Tool de upload de arquivo completa** (presigned URL → PUT → attach), em vez de obrigar o
    consumidor a sair do MCP com `curl`/HTTP manual. Encapsularia também as pegadinhas: URL expira
    em 300s, o campo a reusar é `storage_path` (não `upload_url`), e o valor no card é lista no
    `createCard` e string no `updateFieldsValues`. *(AON, Siniestros)*
23. **Permitir criar card com campo de anexo obrigatório vazio e anexar depois** — ou documentar
    de forma proeminente que o upload precisa ser resolvido antes do `createCard`. *(Siniestros)*
24. **`update_phase_field` intermitente**: falhas não determinísticas ("Acesso negado"/"Field not
    found") em campos específicos, com campos idênticos do mesmo formulário funcionando. Sem
    contorno conhecido além de tentar mais tarde. *(Siniestros)*
25. **"Acesso negado" transitório** em `get_automations`/`get_ai_agents` sobre recurso
    comprovadamente acessível (a mesma chamada funciona minutos depois, sem mudança). Investigar
    causa; hoje o único contorno é retry tardio. *(Siniestros)*
26. **Documentar o formato string de `expressions_structure`/`structure_id`** (`"0"`, não `0`) no
    schema da condicional. *(Siniestros)* **[validado ao vivo]**
27. **Documentar a indexação de condicionais sob a fase Start form.** `get_field_conditions(phase_id=X)`
    retorna vazio para a fase X mesmo quando ela tem condicionais em efeito; todas vivem sob o
    `phase_id` do Start form, e `phases[].fieldConditions` no GraphQL retorna vazio sempre
    **[validado ao vivo]**. A description da tool ("Phase ID that owns the condition") induz a
    diagnóstico errado. *(Onboarding, Siniestros)*
28. **Trilha de auditoria de campo deletado** (`get_field_history` ou similar): "este `internal_id`
    existiu? quando foi apagado?" — teria acelerado o diagnóstico de uma automação com gatilho
    órfão que exigiu enumerar todos os campos do pipe. *(Onboarding)*
29. **`execute_graphql` com paginação/truncamento inteligente** para respostas grandes, em vez de
    falhar com "exceeds maximum allowed tokens" — ou ao menos sugerir no erro uma query filtrada
    pelos ids pedidos. *(Firmas e Poderes)*
30. **Preview de Pipe Report** (algumas linhas renderizadas) para validar que colunas calculadas
    populam antes de dar a tarefa por concluída. *(Onboarding)*

## 4. Tabelas (databases) e visão de eventos

31. **Permissões/membros de database**: não há como consultar se uma conta de serviço (ex.: a de
    uma conexão iPaaS) tem escrita numa tabela — a causa raiz de um `PERMISSION_DENIED` em produção
    só pôde ser inferida indiretamente. Algo como `get_table_members`/`get_table_permissions`.
    *(KYC Sócios)*
32. **Listar/filtrar `table_records`** (por valor de campo, ex.: CNPJ) — necessário para verificar
    duplicidade de registros de cache após reprocessamento; hoje não há caminho. *(KYC Sócios)*
33. **Visão unificada "tudo que reage a eventos deste pipe"** — automações nativas, behaviors de
    agentes, AI automations e webhooks (com destino) numa resposta. O gerador real de um campo
    ("Resultado Consolidado HTML") era um flow iPaaS invisível a `get_automations`/`get_ai_agents`/
    `get_ai_automations`; só `get_webhooks` deu a pista. *(Firmas e Poderes)*

## 5. Para o repositório `skills_ipaas` (fora deste repo, encaminhar separado)

- **Truncamento de 6.000 caracteres na CLI `ipaas_client.py`** corta JSON no meio e corrompe o
  parse; truncar preservando JSON válido ou documentar o uso direto da classe `Client`. *(KYC)*
- **Documentar `POST /api/v1/flow-runs/{id}/retry`** (strategies `FROM_FAILED_STEP` |
  `ON_LATEST_VERSION`, `projectId` no body) — é o caso "corrigi a permissão, reprocessa o card que
  falhou", muito comum e ausente da skill. *(KYC)*
- **Aviso: as duas estratégias de retry não são mutuamente exclusivas** — cada chamada é execução
  real e paga; rodar as duas em sequência processou um card duas vezes (consultas a bureaus em
  dobro). *(KYC)*
- **Escopo de projeto do token/.env**: o `PIPEFY_REPO_ID` default aponta para um projeto; operar
  outro pipe exige `--repo` explícito — documentar para evitar investigar o flow errado. *(KYC)*
- **Estrutura real do step de código**: o fonte vive em `settings.sourceCode.code`, não em
  `settings.input.sourceCode.code` como a referência sugere. *(Firmas e Poderes)*
