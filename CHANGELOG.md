# Changelog

## [3.2.0] — 2026-08-31 — a rodada dos relatórios de campo

Primeira rodada alimentada por uso real em escala: nove relatórios de builds e diagnósticos de
consultores (Onboarding PJ/PF, Siniestros Chile, Bemol CGI Garantias, AON Endoso, Ecom Energia,
POC de compras, agentes com MCP tools, Firmas e Poderes, campo dinâmico) mais dois feedbacks
estruturados. Toda mudança de query e as afirmações de schema mais arriscadas foram **validadas ao
vivo** contra um pipe de testes antes de entrar nos arquivos — a régua que a 3.1 criou para o iPaaS
("teste como portão") aplicada à própria documentação do conector.

As sugestões dos relatórios dirigidas ao servidor MCP (não à skill) foram consolidadas em
`feedback/mcp-engineering-2026-08.md`, para encaminhamento à engenharia.

### Corrigido
- **`title_field_id` aceita somente o slug do campo, não o `internal_id`.** A receita da seção 6
  do `graphql-recipes.md` ensinava o formato errado; três builds independentes tropeçaram nisso.
  Verificado ao vivo: internal_id → `Field not found`; slug → sucesso. O campo de título atual
  agora é legível (`title_field`) na query de auditoria.
- **Criação de template de e-mail não existe.** `connector-rules.md` §4.1 e o passo 7 do Builder
  afirmavam que a API "cria e envia"; a introspecção completa do schema num build real provou que
  não há mutation de criação — duas automações foram desenhadas sobre a premissa errada. O guia
  agora manda entregar o conteúdo pronto para colar (assunto + corpo) e criar a automação de envio
  na retomada, quando o template existir na UI.
- **A ligação de fases também é aplicada pela API.** O material sugeria que a restrição era só da
  aba Fluxo da UI; `moveCardToPhase` para fase não ligada é **recusado pela API** (verificado com
  card real). A pendência manual continua a mesma — a correção é na expectativa de contorno.
- **O modelo de ancoragem de condicional estava errado.** A plataforma indexa **toda** condicional
  sob a fase virtual Start form: o atributo `phase` aponta para lá em todas, e o aninhamento
  `phases[].fieldConditions` volta **vazio** mesmo em pipe cheio de regras (verificado ao vivo).
  Dois builds diagnosticaram errado por isso — um criou condicional duplicada, outro reportou
  "condicional no formulário inicial" como defeito. A ancoragem real está nas **ações**
  (`actions[].phase`/`phaseField`), agora lidas pela própria query de auditoria; `diagnostico.md`,
  `02-builder.md` e `03-conferencia.md` foram reescritos nesse modelo.
- **"Campo dinâmico" não é `statement`.** Pedido de conteúdo dinâmico construído como `statement`
  gerou campos que a API confirma e a UI não renderiza (2 relatos; um exigiu recriação manual de
  todos). O tipo correto é **`dynamic_content`** — validado ao vivo por criação, releitura e
  remoção. O defeito de renderização do `statement` via API fica registrado como armadilha.

### Adicionado
- **O formulário inicial é uma fase oculta (`startFormPhaseId`)** — a armadilha mais cara da
  rodada: 13 campos criados na primeira fase visível, pipe entregue com start form vazio, e o
  defeito atravessou **toda** verificação automatizada (só o consultor pegou, na UI). A query
  `AuditPipe` agora traz o id da fase oculta; o Builder cria os campos da "Fase 0" nela; a
  conferência ganhou o lint **"formulário inicial vazio = divergência crítica"**; e a criação de
  condicional deixa de exigir adivinhação de id (era "id da primeira fase − 1" na tentativa e erro).
- **`AuditPipe` v2** (exercitada ao vivo, ponta a ponta): `startFormPhaseId`, `title_field`,
  `webhooks` (o rastro de integrações externas), `parentsRelations`/`childrenRelations` (conexões
  do pipe) e condicionais com expressões **e ações** (campo afetado, fase, ramo `whenEvaluator`) —
  a mesma 1 chamada passa a sustentar os lints da conferência e a varredura da porta A, sem
  `get_field_condition` por suspeita.
- **`connector-rules.md` §4.7 — Agentes de IA**, consolidando 6 relatos: `update_ai_agent` é
  replace-all (apagou behaviors em produção); `id`/`referenceId` não voltam no payload; limite de
  10.000 caracteres por instrução; criação que falha deixa agente parcial (corrigir por update,
  nunca recriar); `validate_ai_agent_behaviors` é lint, não portão; behavior exige **gatilho
  discreto** (select dedicado ou entrada na fase — `field_updated` de anexo não valida);
  `%{action:...}` é a plataforma que insere ao salvar; agente se constrói na aba de Agentes, nunca
  como automação "peça a IA"; e agente com ação de MCP tool (Slack, Docs) é só-UI — vira
  entregabilidade Manual já no spec.
- **`connector-rules.md` §4.8 — Anexos**: o fluxo completo presigned URL (expira em 300s) → PUT
  fora do MCP → `storage_path` (nunca `upload_url`), os formatos divergentes por mutation
  (`createCard` = lista, `updateFieldsValues` = string), upload obrigatório **antes** do card
  quando o anexo é required, e a pegadinha do filename com acento no shell.
- **Compatibilidade evento×ação validada no Planner**: `get_automation_events` +
  `get_automation_actions` entram no contrato de entregabilidade — o catálogo é mais restrito do
  que parece (mover card não aceita `field_updated`; `distribute_assignments` não aceita
  `card_created`) e 2 de 4 automações de um spec aprovado se revelaram inconstruíveis só no build.
- **Conferência read-only nominal**: um subagente de conferência **desativou os 2 agentes de IA do
  cliente** como efeito colateral de exploração. O playbook agora proíbe nominalmente
  `create_*`/`update_*`/`delete_*`/`toggle_*`, e o prompt que o orquestrador monta (SKILL.md,
  etapa 3) carrega a instrução de somente leitura. A conferência também passa a comparar os
  **campos de saída** de cada behavior com o spec (agente que omitiu campo de saída passou
  despercebido em build real).
- **Porta A: varredura de integrações e agentes** — fecha o gap registrado desde a 3.0: campo
  alimentado por receita/flow/webhook inexistente (2 campos plantados de propósito num teste
  passaram batidos), gerador externo invisível (um "Resultado HTML" só localizável pelos
  webhooks), flow iPaaS publicado com runs falhando, **gatilho órfão** de automação
  (`triggerFieldIds` apontando para campo apagado) e **prompt de agente frágil** (critério
  "permite" lido como "exige" gerou falso positivo em produção). O As-is passa a inventariar
  conexões e webhooks — e a porta C ganha a regra de não propor estrutura paralela ao que já
  existe (um pipe auxiliar redundante com um database conectado precisou ser desfeito).
- **Grupos de condição**: if-true e if-false no mesmo grupo (todas as condicionais de um build
  saíram erradas assim) vira armadilha documentada, com verificação pelo ramo `whenEvaluator` na
  releitura.
- **Spec de agente ganha coluna Gatilho** (`handoff-schemas.md`), e o Builder ganha o guardrail:
  estrutura fora do spec é **pergunta ao consultor**, não desvio registrado depois do fato.
- **Planner anti-capitulação**: contestação do consultor se responde com análise contra o as-is e
  o conhecimento — nem "ótimo ponto" reflexo, nem teimosia.
- Armadilhas menores documentadas em §4.4: `create_pipe` ignora `phases`; `event_params.phase` é
  legível mas não escrevível; shapes de escrita de automação que funcionaram
  (`extra_input.event_params.triggerFieldIds`, `strategy` como enum); config de
  `distribute_assignments` ilegível; "Acesso negado" transitório; `delete_phase_field` =
  `pipe_uuid` + slug (verificado ao vivo); `expressions_structure` é string; erro de `create_card`
  aponta para o sintoma errado (`field_value` é LIST). Em `ipaas.md`: reexecutar run é execução
  real e paga, e estratégias de retry não são mutuamente exclusivas (um card foi processado em
  dobro por testar duas em sequência).

### Conhecido / ainda não coberto
- Da lista da 3.1, seguem em aberto: a receita de mutation com forma errada (neutralizada pela
  regra de introspecção), a arquitetura MAIN + SUBFLOW, o export de flow como portador de segredo,
  a nomenclatura documentada ≠ praticada, o cruzamento campo destino × formato do payload e a
  tabela `FieldTypeId` parcial. O item "porta A não vê iPaaS" desta lista **foi fechado** nesta
  rodada.
- **Campo `connector` criado via API pode nascer quebrado na UI** ("We're sorry, something went
  wrong") sem nenhum sinal detectável por leitura — documentado como armadilha com verificação
  visual obrigatória, mas sem detecção automatizável até a plataforma expor um health-check.
- **`statement` via API não renderizar na UI** segue sem causa confirmada pela plataforma — a
  skill contorna (usa `dynamic_content` para conteúdo dinâmico e exige verificação visual), não
  resolve.
- A porta A lê estado e histórico de flows iPaaS, mas **não executa runs** — comportamento segue
  sendo evidência do teste funcional.
- A ordem/posicionamento de fases novas inseridas em pipe existente (porta C) ainda depende de
  ajuste fino na UI em alguns casos relatados — não investigado nesta rodada.

## [3.1.0] — 2026-08-26 — iPaaS ancorado em evidência, e o teste como portão

A maior rodada de iPaaS desde a 3.0.0, construída sobre quatro fontes de evidência, na ordem em que
apareceram: um relatório de diagnóstico de um build real de integração; a auditoria de 13 flows
iPaaS de produção (155 steps, base Activepieces); a leitura do catálogo iPaaS do host (41 tools) e
do `ai-toolkit`; e, já no fim da preparação, a auditoria de um flow construído com esta própria
versão — que expôs cinco defeitos e mudou a conclusão da rodada.

Esse último ponto é o que dá forma ao resto. A rodada começou apostando em **enumerar os shapes
certos** em tabelas de referência. O flow auditado mostrou que dois dos cinco defeitos vinham
justamente de tabela errada ou mal escopada: a aposta falha quando a documentação erra. Uma run
bem-sucedida, ao contrário, converte toda pergunta de shape em passa/não passa e não depende de a
documentação estar certa. Por isso as tabelas ficaram, mas **o teste deixou de ser opcional**.

### Corrigido
- **A regra de aspas paralisava o build.** A proibição de `'` e `"` em "qualquer valor de step",
  introduzida na 3.0.0, alcançava também as expressões — e **100% dos data pills reais** (375
  ocorrências, 176 únicas, nos 13 flows) usam a forma `{{step_3['output']['data']['campo']}}`, com
  aspas simples e notação de colchete. Nenhuma expressão do corpus é livre de aspas, e nenhuma usa
  notação de ponto. Cumprida à risca, a regra tornaria todo data pill uma pendência manual da UI e a
  skill nunca entregaria uma integração; ela também inviabilizava os steps de código, que são
  JavaScript. A regra passa a ter três lados, em `connector-rules.md` §4.6, `ipaas.md` e
  `handoff-schemas.md`: **proibida em texto livre** (nome, mensagem, template, assunto, payload
  textual), **obrigatória em expressão/data pill e em código**, e **nunca aninhada** — ver a regra
  de literal em Adicionado.
- **A afirmação de validação das receitas GraphQL era falsa, e bloqueava a checagem que pegaria o
  erro.** O `graphql-recipes.md` abria com "nunca introspecte o schema em runtime: as formas abaixo
  já foram validadas contra a API". Uma das receitas de mutation está errada — e o flow auditado não
  adivinhou a grafia, **copiou a receita**. A frase foi substituída por uma regra calibrada: as
  queries de leitura podem ser reusadas direto; **toda mutation exige, antes do primeiro uso num
  build, introspecção do input e do tipo de item de cada lista que ela receba** — o erro mora um
  nível abaixo do input principal, onde a introspecção do input não chega. Exemplo de receita deixa
  de ser autoridade sobre o schema. Nenhuma receita foi reescrita: o mecanismo passa a verificar.
- **O teste era opcional para flow sem efeito externo** ("pode ser testado"), o que na prática
  autorizava publicar sem nunca executar — foi exatamente o que aconteceu com o flow auditado, que
  estava publicado com zero runs. Passa a ser obrigatório: `ap_test_flow` ou `ap_test_step`, e
  **zero runs = não publica**, mesmo com go-live aprovado e validação verde. Registrado também no
  `SKILL.md` como pré-requisito técnico, ao lado dos três portões de aprovação.
- `connector-rules.md` §4.2 — registrado que **`getCardById` já devolve todos os campos do card,
  customizados incluídos**, indexados por fase e por slug:
  `data.card.fields_by_phase.<fase>.fields.<slug>.<propriedade>`, com os metadados
  `field`/`phase_field`. Não hipotetizar limitação de leitura de campo — a hipótese não verificada
  consumiu um build inteiro em tentativa e erro. O tom sobre `custom_api_call` fica calibrado: ele é
  legítimo para o que a piece não cobre (8 usos no corpus) e só é errado como contorno de limitação
  não comprovada.
- `connector-rules.md` §4.6 — o item de data pill sem procedência passa a apontar para a ordem de
  evidência do passo 1.5 de `ipaas.md`, em vez de listar as três fontes como alternativas
  equivalentes. Reforça que o que é derivável do schema nunca se descobre por execução.

### Adicionado
- **Ordem de evidência obrigatória para data pills** (`ipaas.md`, passo 1.5): (a) campo Pipefy
  resolve **sempre** pela leitura do pipe (`AuditPipe`, `get_phase_fields`,
  `get_start_form_fields`), nunca por teste do step; (b) campo de piece resolve pelo
  `inputSchema`/`outputSchema` do catálogo iPaaS; (c) amostra de execução controlada só na ausência
  de (a) e (b). Testar step atrás de step para descobrir o que existe era a origem dos timeouts.
- **Duas tabelas de consulta direta**, para não reintrospectar o schema a cada build:
  **`FieldTypeId` → propriedade de `CardField`** e **envelope de saída por step**, extraída dos
  flows de produção. O envelope não é uniforme: `custom_api_call` embrulha a resposta num **nível
  `body` a mais** que as ações nativas, trigger de webhook entrega em `body`, flow chamável e
  chamada de subflow em `data`, e step de código, store e busca em tabela direto em `output`.
- **As duas convenções de indexação** que convivem: campo de card é indexado por **slug**
  (`fields.<slug>.value`), célula de tabela por **id do campo** (`cells.<id>.value`). Trocá-las
  quebra o path silenciosamente.
- **O envelope vale dentro do step de código.** O `inputs` é montado pelas mesmas expressões e
  carrega o mesmo envelope; mapeado sem o nível `data`, chega `undefined` e o código segue rodando
  com o default. Dois erros nomeados como checklist: **campo de card não é array** (é map por slug —
  iterar com `Object.entries`, nunca `.map()`) e **o rótulo não está no topo** (mora em
  `field`/`phase_field`; `f.name` devolve `undefined` e a saída vem com rótulos em branco). E o
  ponto que amarra tudo: `|| {}` e `|| []` num step de código são **silenciadores de erro** —
  transformam path errado em saída vazia plausível, então quem os usa não pode pular o teste.
- **Data pill nunca entra dentro de literal.** Não interpolar `{{...}}` em string JSON, em GraphQL
  montado como texto, nem em qualquer valor entre aspas. O motivo não é o texto que o builder
  escreve: é o valor que chega em runtime — valor de campo do cliente pode conter aspa, barra
  invertida ou quebra de linha, e nesse instante a string que o envolve termina antes da hora,
  invalidando o payload ou fazendo o conteúdo ser lido como parte da consulta. Ordem de escolha:
  ação nativa da piece, variável de GraphQL, nada. Montar a string "com cuidado" é a opção que já
  quebrou.
- **Ação nativa antes de `custom_api_call`, como passo verificável** (`ipaas.md`, passo 1). Antes de
  recorrer à chamada crua ou a step de código para falar com o Pipefy, rodar `ap_research_pieces` e
  registrar nas decisões fechadas qual lista de ações foi lida e o que faltava nela. Sem esse
  registro a escolha é indefensável na conferência.
- **`valid: true` é declarado falso verde**, em `ipaas.md`, `02-builder.md` e `03-conferencia.md`.
  Validação estrutural confere que os steps estão configurados, **nunca** que os dados atravessam: o
  flow auditado reportava `valid: true` em todos os steps com quatro defeitos que uma única run
  teria exposto. A conferência passa a tratar flow publicado com zero runs como divergência alta, e
  a checar `skip: true` — step desativado existe, valida e nunca executa.
- **`shape_verified` exige run.** A marca não é auto-declarada: significa **run com id e status de
  sucesso cuja saída confere com o spec**. Sem run, tudo é `shape_unverified`, e flow com essa marca
  não é publicável — a conferência checa por `ap_list_runs`, não pela palavra do builder.
- **O default deixa de ser construir do zero** (`ipaas.md` passo 2, `02-builder.md` passo 12). Três
  caminhos nomeados: flow parecido no mesmo pipe se resolve com `ap_duplicate_flow` +
  `ap_rename_flow` + updates pontuais (o mais barato, porque nenhum payload de flow passa pelo
  modelo, e o caso mais comum na prática); flow novo vai em `ap_build_flow`, numa chamada; flow
  existente se edita no granular, nunca se reconstrói. Registrada a pegadinha do duplicate: ele
  **não copia conexão nem sample data**, então a conexão precisa ser religada pelo `externalId`
  antes de validar — sem isso o flow passa na validação estrutural e falha em execução.
- **`ap_build_flow` não configura router.** Branch e condição não são configuráveis nessa chamada: a
  espinha vai sem router e cada router entra depois com `ap_add_step`, cada branch com
  `ap_add_branch` / `ap_update_branch`. Corrige a expectativa de custo — nos flows auditados há 21
  routers e 26 branches condicionais, e apenas 1 dos 13 caberia numa única chamada de build.
- **Fidelidade ao spec aprovado**: antes de qualquer alteração estrutural num flow com spec
  aprovado, reler a seção 7 do `spec.md` e as decisões fechadas do `changes.md`. Piece ou step
  fechado no spec não é negociável; caminho alternativo só quando o spec genuinamente não cobrir o
  caso, e nesse caso **pergunte ao consultor** em vez de trocar silenciosamente.
- **Coluna Decisões fechadas** no `changes.md`, por flow (`piece ou step escolhido (+ versão) |
  motivo | evidência`). Como a decisão passa a viver em arquivo e não só na conversa, ela sobrevive
  a timeout e reconexão do MCP. A **versão da piece** entra porque envelope e inputs mudam entre
  versões, e um mesmo projeto roda várias em paralelo (a piece Pipefy apareceu em seis versões, de
  0.1.4 a 0.2.0, nos 13 flows).
- `SKILL.md` — duas regras globais: **o schema vem antes do teste** (estrutura de pipe é conhecível
  por leitura; descobrir por tentativa e erro é a via mais curta para o timeout) e **decisão de
  arquitetura mora em arquivo, não na conversa**. Versão do documento atualizada de 3.0 para 3.1.

### Conhecido / ainda não coberto
- **Uma receita de mutation do `graphql-recipes.md` continua com a forma errada**, por decisão
  explícita: a correção desta rodada é o mecanismo de verificação, não o conteúdo. A regra nova
  neutraliza o risco (a introspecção antes do primeiro uso pega a divergência), mas a linha errada
  segue no arquivo. As demais receitas não foram auditadas — a seção 2 foi conferida e está correta.
- **Arquitetura MAIN + SUBFLOW não está na skill.** Nos flows reais, 10 dos 13 triggers são flow
  chamável, com 15 chamadas de subflow e 17 respostas de retorno: o padrão é 1 MAIN orquestrando N
  subflows por entidade, e o contrato de entrada de cada subflow é declarado no próprio flow
  (`exampleData`) — uma fonte de schema que a ordem de evidência ainda não conhece. A skill hoje só
  descreve flow monolítico. Idem para os tipos de step não-piece: 21 roteadores, 23 steps de código
  e 7 loops, ou seja **51 dos 142 steps** do corpus.
- **O export de flow é artefato portador de segredo.** Um trigger de webhook do corpus carrega
  usuário e senha literais, e os `exampleData` carregam CNPJ, razão social e e-mail de cliente real.
  A skill proíbe persistir segredo em handoff, mas ainda não avisa que ler um export e resumi-lo
  vaza credencial.
- **A nomenclatura documentada não é a praticada.** `nomenclature.md` define recipe iPaaS como
  `[Fase gatilho] Cenário -> Ação`; os flows reais usam `✅[PRD][3/4 SUBFLOW][CRIAÇÃO] TÍTULO` —
  status, ambiente, ordinal no conjunto, papel, domínio, entidade — com separação de ambiente por
  variável de projeto. Um dos dois está desatualizado; não alterado nesta rodada.
- **Campo destino x formato do payload** não é checado em lugar nenhum. No flow auditado, HTML era
  gravado num campo `long_text`, que armazena texto e não renderiza marcação — o processo poderia
  passar em todos os portões e ainda assim entregar markup cru ao usuário.
- **Não existe export/import de JSON no catálogo iPaaS**, e `ap_flow_structure` trunca. Não há
  leitura fiel do input de um step de piece, o que torna o `spec.md` e o `changes.md` o único
  registro recuperável do mapeamento de data pills.
- O diagnóstico (porta A) segue **sem** listar flows iPaaS e sem verificar histórico de execução —
  um flow publicado e falhando não aparece hoje num diagnóstico padrão.
- A tabela `FieldTypeId` → propriedade cobre os tipos em uso nos builds da BU; tipo raro fora dela
  ainda cai no caminho (c), amostra controlada.

## [3.0.0] — 2026-08-25 — iPaaS de primeira classe

iPaaS (Advanced Automations) passa a ser capacidade de primeira classe do Process Builder para
integrações aprovadas, preservando portões explícitos de segurança e de go-live.

### Adicionado
- `SKILL.md` — habilita o caminho de iPaaS para integrações aprovadas e define aprovações
  **separadas** para build, teste com efeito externo e publicação; nenhuma é implícita nas
  outras. Versão do documento atualizada de 2.0 para 3.0.
- `references/ipaas.md` — playbook autoritativo do fluxo iPaaS: descoberta escopada por
  `pipe_id`, conexões em modo **reuso-somente** (a skill nunca cria/rotaciona credencial),
  ciclo descobrir → construir rascunho → validar → testar → publicar, e recuperação segura após
  erro/timeout (nunca retry cego).
- `references/01-planner.md` e `discovery_questions.md` — discovery passa a captar o contrato
  da integração: pipe dono do flow, evento gatilho, mapeamentos de entrada/saída, conexão
  existente a reutilizar, se o teste pode ter efeito externo, e a intenção de publicação —
  registrado como pendente de aprovação futura, nunca assumido.
- `references/handoff-schemas.md` — novas colunas de iPaaS em `spec.md` (seção 7) e
  `changes.md` (seção 5): pipe dono, trigger, steps/pieces, procedência dos data pills,
  conexões reutilizadas, teste e estado de publicação — sem persistir segredo, token ou
  payload sensível em nenhum handoff.
- `references/02-builder.md` e `connector-rules.md` — execução **catálogo primeiro** (nunca
  carregar o catálogo inteiro, expandir só o `tool_name` necessário), exclusão da criação de
  conexão do escopo do builder, e todo efeito externo (teste ou publicação) atrás de aprovação
  explícita registrada na conversa. `connector-rules.md` §4.6 documenta a proibição de aspas
  simples/duplas em qualquer valor de step iPaaS — comportamento não confiável do transporte MCP.
- `references/03-conferencia.md`, `teste-funcional.md` e `review-completo.md` — cada etapa
  ganha checklist de iPaaS: a conferência confere `flow_id`, conexões e estado de publicação
  contra o spec; o teste funcional só executa efeito externo com aprovação registrada; o review
  completo cobra procedência dos data pills documentada (`shape_verified`) antes de publicar.
- `references/brain-access.md` — nova fonte de grounding, opcional: **padrões de integração**
  (iPaaS blueprints) já resolvidos no brain por app/piece ou tipo de evento. Busca pontual antes
  de desenhar um flow do zero; ausência de resultado não bloqueia nada — o acervo ainda está
  crescendo, e a skill segue direto para a descoberta normal do catálogo.

### Corrigido
- Proibição de aspas (`'`/`"`) em valor de step de flow, antes ausente, agora documentada em
  três pontos do fluxo (`connector-rules.md`, `ipaas.md`, `handoff-schemas.md`) como regra dura
  de planejamento — reescrever sem aspas ou registrar como pendência manual da UI.

### Conhecido / ainda não coberto
- O diagnóstico (porta A) ainda **não** lista flows iPaaS nem verifica histórico de execução —
  um flow publicado e falhando não aparece hoje num diagnóstico padrão. Mapeado para a próxima
  rodada, não escondido.

## [2.0.0] — 2026-08-20 — diagnóstico, custo e proteção de pipe clonado

Baseline conhecido no primeiro commit deste repositório (`3178cc9`).

### Adicionado
- **Porta A (diagnosticar)**: leitura de um pipe existente para achar defeitos, avaliar
  conformidade e sugerir melhorias — **somente leitura**, não altera nada. Vira o ponto de
  entrada também da porta C (evoluir), que usa o diagnóstico como as-is para montar deltas.
- **Disciplina de custo obrigatória**: leitura de pipe em 1 query em vez de N+1 chamadas,
  escrita em lote quando houver receita, e proibição de reler o que já está no contexto.
- **Pendências manuais em destaque na entrega**, com a ligação das fases sempre em primeiro
  lugar quando o build for de pipe novo — a API do Pipefy não a configura, e sem ela o pipe
  nasce com a estrutura completa e nenhum card andando do início ao fim.
- **Protocolo de segurança para pipe clonado** (`connector-rules.md`, seção 5): endereçar
  sempre por `id` (nunca por nome ou slug — idênticos entre original e clone), declarar o pipe
  alvo por id antes da primeira escrita, e reler o pipe original ao final para confirmar que
  nada escapou. Motivado por um incidente real relatado pelo time durante adaptação de um
  template clonado da BU.

## [1.0.0] — data não registrada — versão inicial

Predecessora sem histórico de commit neste repositório; não documentada em detalhe aqui.
