# Regras do connector Pipefy (obrigatórias)

Valem para todas as etapas que tocam o Pipefy via MCP (diagnóstico e Planner em leitura, Builder,
conferência, teste funcional e review). Ignorá-las trava o servidor MCP ou corrompe o pipe do cliente.

## 1. Pré-check de connector e acesso (primeiro passo de qualquer estágio)

Antes de qualquer operação, confirme que o connector do Pipefy está ativo e que você tem
acesso à org de destino com **uma leitura leve e escopada** (ex.: `get_organization` da org
alvo, ou uma leitura escopada do pipe de origem nas portas A e C). Se falhar:

- **Sem connector:** oriente a pessoa a ativar o connector do Pipefy no Claude Code e parar.
- **Sem acesso à org:** oriente a pedir acesso à org de destino do cliente e parar. Nunca
  tente contornar.

As chamadas executam com a credencial de quem está na conversa.

## 2. Nunca faça busca global entre orgs

**Nunca** use `search_pipes` sem filtro nem qualquer busca ampla entre organizações — trava o
servidor MCP por timeout silencioso. Sempre escope por `organization_id` / `pipe_id` / id.

## 3. Cautela com `create_automation`

Payloads com condição composta já travaram o servidor (timeout de ~4 min). Regras:

- Prefira payloads simples; crie com `active=false` para testar antes de ativar.
- Após **qualquer** timeout, verifique com `get_automations(pipe_id=...)` **antes de repetir** —
  evita duplicata.
- Se não der, registre a automação como **pendência manual** no `changes.md` — nunca insista
  às cegas.

## 4. Limites e armadilhas conhecidas (leia antes de descobrir por tentativa e erro)

Este registro existe porque redescobrir os mesmos limites a cada build é a maior fonte de
retrabalho — e retrabalho é custo: cada tentativa falha é um turn que reenvia o contexto inteiro.
Tudo abaixo foi observado em builds reais ou verificado contra o schema.

### 4.1 O que a API realmente não faz → pendência manual

| Item | Situação |
|---|---|
| **Ligar as fases umas às outras** | `cards_can_be_moved_to_phases` **não tem mutation** (verificado em `UpdatePhaseInput`, `SettingsInput` e na lista completa de mutations). Só a aba "Fluxo" da UI configura — **e a restrição vale também na API**: `moveCardToPhase` para fase não ligada é recusado (verificado com card real), não é trava só visual |
| Descrição do pipe | Não existe em `UpdatePipeInput` |
| Template de e-mail | **Sem criação, edição ou exclusão via API** — a introspecção completa do schema confirmou que não existe mutation de criação (o registro anterior de que "criar" era possível estava errado). Só ler e enviar. Automação que dependa de template novo: o template nasce na UI primeiro; deixe o conteúdo pronto para colar (assunto + corpo) na pendência e ofereça criar a automação na retomada, com o `email_template_id` resultante |
| Mover card por mudança de campo | O catálogo de automações não tem a combinação: `move_card`/`move_single_card` só aceitam os eventos `card_moved`/`all_children_in_phase`, nunca `field_updated`. Confira evento×ação em `get_automation_events`/`get_automation_actions` **na etapa de spec** — 2 de 4 automações de um spec aprovado já se revelaram inconstruíveis só no build |
| Agente de IA com ação de MCP tool (Slack, Docs etc.) | `create_ai_agent` aceita só 6 tipos de ação (`update_card`, `move_card`, `create_card`, `create_connected_card`, `create_table_record`, `send_email_template`). O actionType `mcp_tool` existe no produto, mas a amarração com o servidor MCP conectado ao pipe só existe na UI — forçar cria agente meio-configurado que reporta sucesso e não funciona |
| Aplicar etiqueta por automação | A ação não existe no catálogo de automações |
| Restringir quem cria card | `anyone_can_create_card` sem mutation |
| Interfaces / Portais | Não há leitura do **layout atual**, então escrever elemento sem saber as posições produz tela bagunçada. Trate como fora de escopo e liste o que fazer na UI |
| Encadear resposta de chamada HTTP | O corpo da resposta não fica disponível para outra automação decidir. Lógica "consulta base externa e decide" exige **iPaaS**; quando estiver no spec aprovado, siga `ipaas.md` em vez de tratá-la como pendência manual |

> ⚠️ **A ligação das fases é a pendência mais importante de todas.** Um pipe novo nasce com toda a
> estrutura pronta e **nenhum card conseguindo andar do início ao fim** — na prática, inutilizável
> até alguém ligar as fases à mão. É a maior causa de insatisfação com pipes novos. Ela **nunca**
> pode aparecer como uma linha discreta: vai destacada no spec, no changes e na entrega, com a
> lista explícita de quais ligações fazer (origem → destino, na ordem do fluxo).

### 4.2 O que parece não existir, mas existe (não gaste turns tentando contornar)

- **O formulário inicial é uma fase oculta, e o id dela é legível.** O Pipefy modela o start form
  como uma fase virtual ("Start form") que **nunca aparece em `pipe.phases`** — quem constrói um
  pipe do zero tem todo motivo para achar que a primeira fase visível é o formulário, criar os
  campos lá e entregar o pipe com o formulário vazio. **Aconteceu num build real, e o defeito
  atravessou toda verificação automatizada** (o pipe "parece" completo em qualquer leitura de
  `phases`); só apareceu quando o consultor abriu a UI para criar um card. O id dessa fase está em
  `pipe.startFormPhaseId` (incluído na query da seção 1 de `graphql-recipes.md`): é nela que os
  campos da "Fase 0" do spec são criados, e é o `phase_id` que a criação de condicional espera.
  Não deduza esse id por aritmética de ids vizinhos.
- **O campo de título atual é legível:** `pipe { title_field { id internal_id label } }`. A
  escrita (`updatePipe.title_field_id`) aceita **somente o slug** — ver `graphql-recipes.md`,
  seção 6.
- **Segurança do pipe e campo de título:** a tool `update_pipe` aceita só nome/ícone/cor, mas a API
  aceita `public`, `public_form`, `only_assignees_can_edit_cards`, `only_admin_can_remove_cards` e
  `title_field_id` — ver `graphql-recipes.md`, seção 6. **Não é pendência manual.**
- **Condição de disparo da automação:** `get_automations` omite o campo `condition`. A query da
  seção 5 de `graphql-recipes.md` traz. Isso já causou reprovação indevida de um build inteiro.
- **Lote de valores de campo de card:** existe `updateFieldsValues` — seção 7 de `graphql-recipes.md`.
- **`getCardById` já devolve os campos customizados.** O step da piece Pipefy retorna **todos** os
  campos do card, customizados incluídos, indexados por fase e por slug:
  `data.card.fields_by_phase.<fase>.fields.<slug>.<propriedade>`, com os metadados `field`/
  `phase_field` e a propriedade de valor correspondente ao tipo. Comprovado em flows de produção.
  Não hipotetize limitação de leitura de campo nem troque a piece por `custom_api_call` "para
  garantir" — `custom_api_call` é legítimo para o que a piece não cobre (mutation ausente do
  catálogo, por exemplo), não como contorno de limitação que você não comprovou por leitura real.
  Note que ele embrulha a resposta num nível `body` a mais que as ações nativas. O mapa
  `FieldTypeId` → propriedade e o envelope de cada step estão em `ipaas.md`, passo 1.5.

### 4.3 Armadilhas de escrita — verifique **depois** de escrever

- **Condicional fantasma (o pior deles).** `create_field_condition` pode responder "criado com
  sucesso" e a regra **não persistir**. Observado em 5 builds. Depois de criar qualquer
  condicional, releia `pipe.fieldConditions` (a query da seção 1 de `graphql-recipes.md` já traz
  expressões e ações de todas) e confirme que ela existe, com expressões e ações corretas, antes
  de reportar como pronta. Um "sucesso" mentiroso engana você e quem confia no seu relatório.
  **Ao conferir a ancoragem, não use o atributo `phase`:** ele aponta para a fase virtual Start
  form em **toda** condicional do pipe — é assim que a plataforma indexa, e não é defeito (builds
  antigos leram isso como "condicional caiu no formulário inicial" e diagnosticaram errado; um
  deles criou condicional duplicada por causa disso). A ancoragem real está nas **ações**:
  `actions[].phaseField` diz o campo afetado e `actions[].phase` a fase. E `phases[].fieldConditions`
  volta vazio mesmo com condicionais existindo — o aninhamento por fase não serve para nada.
- **Condicional sem valor de comparação.** O `value` da condição fica nulo (ou string vazia) e a
  regra nunca dispara. Preencha sempre o valor de comparação e confirme na releitura.
- **If-true e if-false no mesmo grupo de condição.** Dois desfechos ("se Sim, mostrar X; se Não,
  mostrar Y") são **duas condicionais** (ou dois grupos), nunca duas expressões no mesmo grupo —
  montadas juntas, a regra avalia errado. Já saiu um build com **todas** as condicionais erradas
  assim. O ramo de cada ação aparece em `actions[].whenEvaluator` na releitura: confira que cada
  desfecho está no ramo certo.
- **Campo `connector` criado via API pode nascer quebrado na UI.** A mutation responde sucesso, a
  leitura devolve o campo normalmente, e a UI mostra "We're sorry, something went wrong" no lugar
  do seletor de conexão — **nenhuma leitura via API detecta** esse estado. Depois de criar campo
  conector via API, inclua a verificação visual na UI como pendência explícita da entrega.
- **Agente de IA tem seção própria** — as armadilhas de criação e edição (replace-all, ids, limite
  de instrução, criação parcial, gatilho) estão na **seção 4.7**. A mais urgente: todo agente
  nasce ativo, e editar religa agente desligado.
- **Campo de conexão é replace-all.** Atualizar substitui a lista inteira. Leia a lista atual e
  reenvie completa — e evite mexer quando outra automação puder estar escrevendo no mesmo campo.
- **Erro pode ser falso-negativo.** Já houve `success: false` com mensagem vazia numa operação que
  **foi aplicada** — e o retry duplicou 18 cards. Depois de qualquer erro ou timeout numa escrita,
  releia o estado real antes de repetir.

### 4.4 Limites e formatos

- **~30 campos por chamada** em lote. Quebre em blocos de ~20 para ter margem.
- **Acentos quebram o slug:** "Órgão" gera `rg_o`. Crie o campo com rótulo **sem acento** e ajuste
  para o rótulo final com `update_phase_field` depois — vale para acentos, `/`, `.` e emoji.
- **Enum de SLA é minúsculo** (`late`), embora a documentação mostre capitalizado.
- `delete_phase_field` exige **`pipe_uuid` (formato UUID) + o slug do campo**. `pipe_id` numérico
  dá `PERMISSION_DENIED` e `internal_id` dá `RESOURCE_NOT_FOUND` — erros genéricos que não dizem
  qual formato era esperado. (Verificado ao vivo.)
- **Conteúdo dinâmico/statement tem seção própria (4.9).** O essencial: o tipo certo é
  `statement`, com uma receita exata; `dynamic_content` é aceito pela mutation e **corrompe a
  página de configurações da fase** na UI. Nenhum dos dois defeitos é visível por leitura de API.
- **`expressions_structure` e `structure_id` de condicional são strings** (`"0"`), não números —
  valor numérico é recusado sem mensagem que aponte o motivo.
- **`create_pipe` ignora o parâmetro `phases` silenciosamente** — o pipe nasce com as 3 fases
  default. Crie as fases depois, em lote (`graphql-recipes.md`, seção 3).
- **`event_params` aceita menos na escrita do que devolve na leitura.** `update_automation` recusa
  chaves que `get_automation` retorna (ex.: `phase` → "Field is not defined on
  AutomationEventParamsInput"). Shapes que funcionaram em build real: criar pela tool dedicada com
  `name`/`trigger_id`/`action_id` e completar via `extra_input` com `event_params.triggerFieldIds`
  e `action_params.strategy` (enum `ROUND_ROBIN`/`RANDOM`).
- **Compatibilidade evento×ação é restrita, e só o catálogo responde.** `move_card`/
  `move_single_card` só aceitam `card_moved`/`all_children_in_phase`; `distribute_assignments` só
  `field_updated`/`sla_based`. Por isso a checagem em `get_automation_events` +
  `get_automation_actions` pertence à etapa de **spec** (ver 4.1), não ao build.
- **A configuração real de `distribute_assignments` não é legível** — os campos relevantes voltam
  `null` em qualquer leitura, inclusive no pipe original. Para replicar, recrie com os parâmetros
  declarados; não adivinhe o que a leitura não mostra.
- **"Acesso negado" pode ser transitório.** `get_automations`, `get_ai_agents` e
  `update_phase_field` já falharam com erro de acesso em recurso comprovadamente acessível — e a
  mesma chamada funcionou mais tarde na sessão, sem mudança nenhuma. Antes de concluir falta de
  permissão, tente de novo mais tarde (sem loop de insistência).
- **Mensagem de erro pode apontar para o sintoma errado.** `create_card` devolve "campo
  obrigatório não preenchido" quando o problema real é `field_value` escalar — o tipo é **LIST**
  (`["valor"]`). Diante de erro de negócio incoerente com o que você enviou, introspecte o input
  antes de formular hipóteses de permissão ou estado.
- **Campos arquivados não aparecem** nas leituras: um campo "que não existe" pode estar arquivado.
- **Nomes de parâmetro são inconsistentes** dentro do mesmo input (`triggerFieldIds` em camelCase
  convivendo com `to_phase_id` em snake_case). Confirme em `get_automation_events` e
  `get_automation_actions` em vez de adivinhar a grafia.
- **Logs de agente de IA** podem ficar presos em "processing" sem timeout, e não há como re-testar
  um comportamento sob demanda. Não trate log parado como prova de falha.

### 4.5 Diagnóstico honesto de falha

Se um card não move, a causa quase sempre é **campo obrigatório não preenchido** — inclusive campo
**oculto por condicional**, que continua obrigatório e trava o movimento **sem erro visível** — ou
uma restrição de fluxo. Antes de concluir que "o MCP está fora do ar" ou culpar a infraestrutura,
verifique os campos obrigatórios da fase e `get_phase_allowed_move_targets`. Diagnóstico errado
interrompe o trabalho do consultor por nada.

### 4.6 iPaaS (Advanced Automations)

- iPaaS é acessado pelas meta-tools `get_ipaas_tools`, `call_ipaas_tool`,
  `get_ipaas_connection_auth_url` e `create_ipaas_connection`. Neste builder, use somente descoberta
  e invocação necessárias ao flow aprovado; criação/rotação de conexão é fora de escopo. A existência
  dessas tools no AI Toolkit não autoriza o Builder a receber credenciais ou criar conexões.
- O catálogo, as conexões e os flows são do `pipe_id` dono. Não procure ou opere por nome de pipe,
  nem copie um `externalId` de contexto não confirmado nesse workspace.
- Fluxo seguro: catálogo compacto → schema de uma tool → chamada. Nunca expanda todos os schemas.
- **Aspas: proibidas em texto livre, obrigatórias em data pill.** A regra tem dois lados, e
  confundi-los paralisa o build. Em **valor de texto livre** — nome de step, mensagem, template,
  assunto, corpo de e-mail, texto de payload — não envie `'` nem `"`: o transporte MCP tem
  comportamento não confiável com eles; reescreva sem aspas e, se o valor só funcionar com aspas,
  registre-o como pendência manual da UI. Em **expressão/data pill** é o contrário: a forma
  canônica é `{{step_3['output']['data']['campo']}}`, com aspas simples e notação de colchete, e
  **é a única forma aceita** — todo flow de produção usa exclusivamente ela. O mesmo vale para o
  **JavaScript de um step de código**, que é escrito com aspas normalmente. Não tente "consertar"
  uma expressão removendo as aspas: isso produz data pill que não resolve.
- Depois de timeout/erro em `call_ipaas_tool`, não repita. A ação pode já ter executado; confira flow,
  lista de runs ou run específico e registre a retomada.
- **Expressão sem procedência (data pill no escuro).** Não escreva `{{trigger...}}` ou
  `{{step_...}}` por analogia com outro webhook/piece. Para cada expressão, siga a **ordem de
  evidência** do passo 1.5 de `ipaas.md` — campo Pipefy resolve pela leitura do pipe, campo de piece
  pelo schema dela, amostra de execução só na falta dos dois — e registre no changes qual dessas
  fontes provou o path. Schema de campo Pipefy não prova sozinho o envelope de uma piece externa.
  Sem path comprovado, marque `shape_unverified`, peça autorização para teste controlado se
  necessário e não publique o flow. Validação estrutural não elimina essa pendência.
  **O que é derivável do schema nunca se descobre por execução:** repetir teste de step para
  descobrir quais propriedades existem é a via mais curta para o timeout.
- Conexão ausente bloqueia somente o trecho dependente, não o restante do build. Registre piece,
  finalidade e o link `https://app.pipefy.com/pipes/<pipe_id>/integrations`; não crie um mock que
  pareça flow funcional nem tente criar/rotacionar a conexão.
- Validar rascunho não autoriza teste externo, nem comprova data pills. Testar externamente não
  autoriza publicar. Publicar ou habilitar sem aprovação explícita é mudança indevida. Veja
  `ipaas.md` para o ciclo completo.

### 4.7 Agentes de IA — criação e edição

O objeto com mais armadilhas do conector. Tudo abaixo foi observado em builds reais:

- **Agente se constrói na aba de Agentes (`create_ai_agent`), nunca como automação com ação de
  "peça a IA".** Automação com IA embutida vira caixa-preta fora do padrão da BU e conflita com a
  gestão de agentes — já exigiu refatoração arquitetural inteira de um build.
- **Todo agente nasce ativo, e editar religa.** Um `update` zera o `disabledAt` — um agente que o
  cliente desligou volta a rodar, gastando crédito e agindo nos cards. Se o spec não pede o agente
  ativo, desative logo após criar (`toggle_ai_agent_status`). Na porta C, **registre o estado de
  cada agente antes de editar e restaure depois**. E clonar um pipe **traz junto os agentes
  desativados do original** — inventarie os estados logo após o clone.
- **`update_ai_agent` é replace-all, não patch.** Enviar um subconjunto de `behaviors` **apaga
  silenciosamente os demais** — já custou dois comportamentos de um agente em produção, sem aviso
  nenhum. Antes de editar, leia o agente (`get_ai_agent`) e reenvie o conjunto completo.
- **Não reenvie `id`/`referenceId` de behaviors/actions no payload.** O backend os gera; devolvê-los
  derruba a chamada com o erro genérico "Houve um problema ao salvar o agente" — que não diz a
  causa. O mesmo erro aparece com `value: ""` explícito em `fieldsAttributes`. Diante dele, cheque
  esses dois suspeitos antes de qualquer outra hipótese.
- **Limite de 10.000 caracteres por instrução**, descoberto só no erro ao salvar. Escreva a
  instrução já contando com o teto — não há como consultá-lo pela API.
- **Criação que falha pode deixar agente parcial.** A API chega a gerar o id do agente mesmo com a
  configuração falhando. Depois de qualquer erro em `create_ai_agent`, **liste os agentes antes de
  tentar de novo**: se houver resíduo parcial, corrija por `update` no id existente em vez de criar
  outro — recriar às cegas duplica agente.
- **`validate_ai_agent_behaviors` é lint, não portão.** Ela valida contra um shape que não
  corresponde 1:1 ao tipo real da mutation — "válido" já precedeu falha de criação. Use como
  checagem barata; o sucesso real é criar e **reler**. Se a tool dedicada falhar com erro opaco
  após 2 tentativas, o fallback que funcionou em build real é GraphQL cru, introspectando a cadeia
  `CreateAgentInput` → `AiAgentInput` → `AutomationInput` → `AiBehaviorParamsInput` →
  `AiBehaviorActionAttributesInput` → `FieldMapInput`.
- **Behavior exige gatilho discreto.** O disparo é a entrada do card numa fase ou um campo de
  seleção dedicado (padrão de produção: select Sim/Não do tipo "Iniciar análise com IA");
  `field_updated` direto sobre campo de anexo **não valida no servidor**. O gatilho se fecha no
  spec — se faltar e for preciso criar um campo extra, é pergunta ao consultor, não desvio
  silencioso.
- **`%{action:<referenceId>}` na instrução é gerado pela plataforma.** O id só existe depois de o
  agente ser salvo. Crie o agente **sem** a linha `%{action:...}` — a plataforma a insere ao
  salvar — e confirme por releitura; nunca invente o id.

### 4.8 Anexos — upload e cards de demonstração

Não há tool que faça o fluxo inteiro; são três passos acoplados, cada um com uma pegadinha (tudo
observado em builds reais):

1. `create_attachment_presigned_url` devolve `upload_url` **e** `storage_path`. A URL assinada
   **expira em ~300s** — execute os passos em sequência, sem pausa longa entre eles.
2. O upload é um `PUT` HTTP **fora do MCP** (shell). No Windows, `Invoke-WebRequest` já falhou com
   mensagem enganosa; `System.Net.WebClient.UploadData` com TLS 1.2 explícito funcionou. **Nome de
   arquivo com acento ou caractere especial quebra o upload silenciosamente** (o caractere some no
   argumento do shell e o erro vira "arquivo não encontrado") — copie para um nome ASCII antes.
3. No campo do card entra o **`storage_path`**, nunca a `upload_url`. E os formatos divergem por
   mutation: `createCard`/`fields_attributes` exige **lista** (`["<storage_path>"]` — `field_value`
   é LIST para qualquer tipo de campo); `updateFieldsValues` espera **string simples** com o path.

A ordem importa: **`createCard` recusa card com campo de anexo obrigatório vazio** — não dá para
criar o card primeiro e anexar depois. Resolva o upload antes de criar o card.

### 4.9 Conteúdo dinâmico no card — o tipo é `statement`, e a receita é exata

Bloco somente-leitura renderizado no card (instruções contextuais, resumo de agente, tabela de
histórico, iframe). O caminho aparente pela API está errado, e o certo tem cinco regras não óbvias —
todas descobertas por engenharia reversa (campo criado na UI, lido pela API, replicado atributo a
atributo, variando um por vez). **Nada abaixo é visível por leitura de API**: a escrita responde
sucesso, a releitura confirma, e o comportamento real só aparece na UI.

- **`dynamic_content` é armadilha, não o tipo.** A mutation aceita e cria o campo normalmente — e a
  página de configurações da fase **fica em branco na UI** (a fase inteira deixa de ser editável
  manualmente até o campo ser removido). Não use.
- **O conteúdo vive na `description` do campo, não em valor de card.** `statement` não tem `value`:
  escrever nele via `update_card_field` falha silenciosamente. Conteúdo se altera com
  `update_phase_field` na `description` — ou seja, no nível da fase, não do card.
- **Conteúdo que varia por card = token apontando para outro campo**, no formato
  `{{phase<ID_DA_FASE>.field<INTERNAL_ID>}}` — com **`internal_id`**, nunca slug (slug não dá
  erro; só não substitui).
- **O token só resolve dentro do envelope HTML exato do editor da UI:**
  `<p class="text-editor-paragraph"><span style="white-space: pre-wrap;">{{...}}</span></p>`.
  Fora dele (`<p>` sem a classe, `<span>` sem o style, token fora do span), o token aparece como
  **texto literal** na tela — sem erro, sem log.
- **O `label` precisa seguir o padrão `Statement-<uuid>`.** Com label comum ("Instruções",
  "Aviso"), o campo renderiza como **long-text editável** — o usuário digita em cima do conteúdo.
  O label é usado pelo front-end como discriminador de renderização; avise o cliente que um rename
  aparentemente inofensivo na UI quebra o campo.
- **A `description` renderiza HTML real, sem sanitização.** É o que viabiliza tabela e iframe — e é
  vetor de XSS: campo-fonte editável por usuário, referenciado por token, vira HTML arbitrário
  executado na sessão de quem abre o card. Disciplina obrigatória: **campo-fonte oculto,
  preenchido só por automação/agente controlado**, nunca campo de digitação livre.

Padrão de implementação para conteúdo por card: (1) campo oculto (`short_text`/`long_text`) que
armazena o conteúdo; (2) automação/agente escreve nesse campo; (3) `statement` com label
`Statement-<uuid>` e `description` no envelope exato com o token; (4) condicional de exibição,
quando aplicável. Conteúdo estático por fase dispensa o token: HTML direto na `description`,
alterável a qualquer momento via `update_phase_field`.

O método que destravou isso vale como regra geral: **quando a tool aceita a escrita e o resultado
não confere, o objeto criado pela UI é a fonte de verdade sobre o formato** — crie na UI, leia pela
API, replique exatamente, e só então varie um atributo por vez para separar o obrigatório do
cosmético.

## 5. Pipe clonado — risco de escrever no pipe errado

Cenário: clonar um template (da BU ou do cliente) e adaptar o clone. **Já houve incidente real:**
várias alterações foram aplicadas **no pipe original em vez do clone**, quebrando uma automação de
um pipe vivo — e isso aconteceu mesmo com instrução explícita de mexer somente no id do clone.
Trate este cenário como o mais perigoso de todos.

Dois mecanismos explicam o erro, e os dois têm cura:

**1. O clone é assíncrono e nasce sem ids.** `clone_pipe` retorna o pipe novo com o array de fases
possivelmente **vazio**, porque o Pipefy materializa as fases depois. Se você precisa de um
`phase_id` nesse instante, os únicos ids que você tem em mão são os do **original** — e usá-los
escreve no original. **Cura:** depois de clonar, **releia o clone** (query `AuditPipe` com o novo
`pipe_id`) até as fases existirem, e trabalhe **somente** com os ids que vieram dessa leitura.
Nunca reaproveite `phase_id` ou `internal_id` lidos antes do clone.

**2. Slugs e rótulos ficam idênticos nos dois pipes.** O clone copia os nomes, então "Fornecedor"
existe nos dois com o mesmo slug. Qualquer resolução de objeto por **rótulo ou slug** é ambígua e
pode acertar o pipe errado. **Cura:** endereçe **sempre** por `internal_id` (campos) e `phase_id`
(fases), lidos do pipe alvo. Rótulo serve para conversar com humano, nunca para endereçar objeto.

### Protocolo obrigatório quando houver clone envolvido

- **Confirme o alvo antes da primeira escrita.** Leia o pipe alvo e declare na conversa
  **nome + id**. Se existir um pipe de nome parecido — tipicamente o original — diga explicitamente
  qual dos dois é o alvo. Nome não identifica pipe; id identifica.
- **Guarde o snapshot do original também**, não só do alvo. É o que permite provar o que escapou e
  reverter.
- **Verifique o raio de alcance no fim.** Terminado o trabalho, rode uma leitura do **original** e
  compare com o snapshot dele. Se qualquer coisa mudou lá: **pare, registre exatamente o que mudou**
  (fase, campo ou automação, com id) e **avise imediatamente** o responsável pelo pipe. Não tente
  consertar sozinho sem confirmação — pipe vivo de cliente ou template de BU afeta outras pessoas.
- Enquanto o raio de alcance não passar, trate cada escrita como irreversível.

## 6. Operações que preservam dados

- Nunca delete fase ou campo com cards/dados sem confirmação explícita. Default = renomear/
  inativar com tag `[Inativo]`.
- Idempotência: antes de criar (fase, campo, automação), cheque por nome se já existe —
  retomadas de build não podem duplicar.
- Nunca duplique/clone campos (quebra IDs). Crie com rótulo limpo (sem `/`, `.`, emojis) e
  renomeie via `update_phase_field` quando precisar do rótulo final.
