# Playbook — iPaaS (Advanced Automations)

Use este playbook somente quando a integração estiver no `spec.md` aprovado. iPaaS é a camada de
fluxos que conecta Pipefy a sistemas externos; não confunda com automações nativas do pipe ou
agentes de IA.

## Pré-check e escopo

1. Confirme o connector Pipefy e o `pipe_id` que será dono do fluxo. Workspace, catálogo, flows,
   conexões e execuções são sempre escopados por pipe.
2. Rode `get_ipaas_tools(pipe_id)` para confirmar que iPaaS está habilitado e que o consultor tem
   permissão de criar automações nesse pipe. Se falhar por plano, feature desabilitada ou permissão,
   não tente contornar: registre a pendência com a mensagem devolvida pelo MCP.
3. Nunca carregue o catálogo inteiro no contexto. Para cada ação, descubra o catálogo compacto,
   expanda somente o `tool_name` que será usado e monte os argumentos a partir do `inputSchema`.

## Conexões

O builder trabalha em modo **reutilizar somente**. Antes de configurar qualquer passo, levante
**todas** as conexões exigidas pelo flow — inclusive a conexão Pipefy do trigger, além das conexões
dos apps externos — e use a tool de listagem de conexões do catálogo para conferir se há uma
conexão compatível para cada uma.

Na porta C, o Planner faz esta pré-checagem de leitura antes da aprovação do spec, pois o pipe já
existe. Na porta B, o Builder a executa imediatamente após criar o pipe, antes de qualquer passo
externo. O toolkit também expõe `create_ipaas_connection` e a jornada OAuth correspondente, mas
essas tools ficam deliberadamente fora do escopo deste builder: lidam com credenciais e rotação de
segredos, e exigem um fluxo de autorização próprio.

- Havendo uma única conexão adequada, registre seu `externalId` no build e use-a.
- Havendo mais de uma, apresente as opções ao consultor; não escolha silenciosamente.
- Não havendo conexão adequada, não peça, aceite, armazene, crie nem rotacione credenciais. Registre
  no `changes.md` a conexão/piece e a finalidade necessárias, deixe somente esse item como parcial e
  dê o link acionável `https://app.pipefy.com/pipes/<pipe_id>/integrations` para o responsável
  configurá-la na UI ou por processo autorizado. Sem todas as conexões requeridas, não construa um
  flow "mock" como se ele funcionasse: entregue o blueprint dos passos e mapeamentos para retomada.
- Nunca copie segredo, token, URL OAuth de retorno ou conteúdo sensível para arquivos de handoff.

## Ciclo de vida do fluxo

1. **Descobrir.** Pesquise as pieces e leia os schemas de trigger, ações, conexões e opções que o
   spec exige. Use valores de opção, não rótulos, quando o catálogo os resolver.

   **Ação nativa antes de `custom_api_call` — e isso é um passo, não uma preferência.** Antes de
   escolher `custom_api_call` ou um step de código para falar com o Pipefy, rode
   `ap_research_pieces` na piece e leia a lista de ações. Só siga para a chamada crua se **nenhuma**
   ação nativa cobrir o caso, e **registre nas decisões fechadas qual lista você leu e o que faltava
   nela**. Sem esse registro, a escolha é indefensável na conferência. Ação nativa recebe valor como
   campo estruturado, dispensa escape e devolve envelope previsível; chamada crua reintroduz os três
   problemas de uma vez. Já houve flow que montou `updateFieldsValues` à mão existindo ação nativa
   de escrita de campo — e errou nome de campo, cardinalidade e escape na mesma linha.
1.5 **Comprovar a origem dos data pills — em ordem de evidência.** A regra vale para **todo** valor
   `{{...}}` que venha do trigger ou da saída de qualquer step anterior, não apenas para o trigger.
   A ordem abaixo não é preferência, é obrigação: só desça um nível quando o anterior genuinamente
   não responder.

   **(a) Campo do Pipefy** (trigger, card ou fase) → resolva **sempre** pela leitura do pipe:
   `AuditPipe` em 1 chamada, ou `get_phase_fields` / `get_start_form_fields` para um recorte pontual
   (`graphql-recipes.md`, seção 1). **Nunca por teste do step.** Se o campo existe no pipe, o
   `FieldTypeId` dele já determina qual propriedade de `CardField` vem preenchida — a tabela abaixo
   fecha isso. O shape é estrutural: não há nada a descobrir por execução.

   **(b) Campo de piece ou action externa** → `inputSchema` / `outputSchema` da piece no catálogo
   iPaaS, ou a documentação dela. Expanda o schema apenas do `tool_name` que você vai usar. Schema
   de campo Pipefy não prova sozinho o envelope de uma piece externa.

   **(c) Só na ausência de (a) e (b)** → amostra de execução controlada. Marque a expressão
   `shape_unverified` até a amostra confirmar e pergunte ao consultor antes de executar; se o teste
   disparar escrita, mensagem ou outro efeito externo, ele continua sujeito à aprovação específica
   e a dados descartáveis. Não teste por rotina quando a fonte já for (a) ou (b).

   Testar step atrás de step para descobrir quais propriedades existem é a maior causa de timeout
   num build de integração — e é sempre evitável quando a fonte é (a) ou (b). Nunca publique flow
   que ainda tenha expressão `shape_unverified`.

   **`FieldTypeId` → propriedade de `CardField`.** É a propriedade que carrega o valor de cada campo
   do card. `getCardById` devolve **todos** os campos, customizados incluídos, indexados por fase e
   por slug — `data.card.fields_by_phase.<fase>.fields.<slug>.<propriedade>` (ver
   `connector-rules.md`, seção 4.2). Consulte aqui em vez de reintrospectar o schema GraphQL a cada
   build:

   | Tipo do campo (`FieldTypeId`) | Propriedade a usar |
   |---|---|
   | `short_text`, `long_text`, `statement`, `email`, `phone`, `cpf`, `cnpj`, `id`, `time` | `value` |
   | `select`, `radio_horizontal`, `radio_vertical` | `value` (opção selecionada) |
   | `number`, `currency` | `float_value` (`value` traz o mesmo como texto) |
   | `date` | `date_value` |
   | `datetime`, `due_date` | `datetime_value` |
   | `attachment` | `array_value` (lista de URLs) |
   | `checklist_horizontal`, `checklist_vertical` | `array_value` (itens) |
   | `connector` (campo de conexão) | `array_value` (ids) + `connectedRepoItems[]` para os dados do item ligado |
   | `label_select` | `array_value` + `label_values[]` |
   | `assignee_select` | `assignee_values[]` |

   `native_value` traz a forma bruta de qualquer tipo e serve de fallback quando a propriedade
   tipada vier vazia; `report_value` só aparece em campo derivado de relatório. Os metadados `field`
   e `phase_field` de cada campo dão id, `internal_id` e rótulo. Endereçe o campo pelo **slug**, que
   você lê no pipe — nunca por posição nem por rótulo.

   **Envelope de saída por step.** O envelope é o que a IA mais alucina, e ele não é uniforme: cada
   ação embrulha o resultado de um jeito. Os paths abaixo foram extraídos de flows de produção e
   valem como fonte (b) — não teste step para redescobri-los:

   | Step | Envelope de `output` |
   |---|---|
   | `pipefy:getCardById` | `data.card.fields_by_phase.<fase>.fields.<slug>.<propriedade>` |
   | `pipefy:getCardsByFieldValue` | `data.cards[]`, e dentro de cada card `fields.<slug>.value` |
   | `pipefy:createCard` | `data.createCard.card.id` |
   | `pipefy:custom_api_call` | `body.data.<mutation>.…` — **um nível `body` a mais** que as ações nativas |
   | trigger de webhook | `body.<…>` |
   | trigger de flow chamável e a chamada de subflow | `data.<…>` |
   | step de código, leitura de store, busca em tabela | direto em `output`, sem envelope |
   | helpers de data | `output.result` · leitura de arquivo: `output.text` |
   | loop sobre itens | `output.item` (o item da iteração corrente) |

   Duas convenções de indexação convivem e trocá-las quebra o path: **campo de card é indexado por
   slug** (`fields.numero_pedido.value`), **célula de tabela é indexada por id do campo**
   (`cells.eQygQ1lXMnU0M8lOjVYf6.value`). Slug vem da leitura do pipe; id de campo de tabela vem da
   leitura da tabela.

   **O envelope vale dentro do step de código também.** O `inputs` de um step de código é montado
   pelas mesmas expressões, então ele carrega o mesmo envelope: se o input foi mapeado de
   `step_1['output']` sem o nível `data`, a variável chega `undefined` e o código segue rodando
   com o default (`|| {}`, `|| []`), produzindo saída vazia sem erro nenhum. Dois erros que se
   repetem, e valem como checklist antes de escrever a primeira linha de JS:

   - **Campo de card não é array.** `fields` é **map indexado por slug** — itere com
     `Object.entries`, nunca com `.map()`. `.map()` num objeto lança `TypeError`; combinado
     com um `|| []` defensivo, não lança nada e devolve vazio.
   - **O rótulo do campo não está no topo.** `CardField` não tem `name` nem `label` — eles
     moram nos metadados `field` / `phase_field`. Ler `f.name` devolve `undefined`, e o
     resultado sai com rótulos em branco em vez de falhar.

   Um `|| {}` ou `|| []` num step de código é um **silenciador de erro**: ele transforma path
   errado em saída vazia plausível. Se você usar um, o teste do passo 4 deixa de ser opcional para
   aquele step — é a única coisa que distingue vazio legítimo de path errado.

   **Fixe a versão da piece.** Envelope e inputs mudam entre versões, e um mesmo projeto costuma ter
   várias em uso ao mesmo tempo. Registre a versão de cada piece no `changes.md` junto da decisão
   fechada: a tabela acima só vale para a versão que você leu no catálogo.
2. **Construir rascunho.** Crie ou altere somente os flows e passos explicitamente aprovados no spec.
   Registre `flow_id`, trigger, pieces e status de validade retornado.
   **Escolha o caminho antes de escrever.** São três, e o default não é construir do zero:

   - **Flow parecido com um que já roda no mesmo pipe → duplique e adapte.** `ap_duplicate_flow`,
     `ap_rename_flow` e depois `ap_update_step` / `ap_update_trigger` pontuais. É o caminho mais
     barato de todos, porque nenhum payload de flow passa pelo modelo — e é o caso mais comum na
     prática (variante de ambiente, mesma integração para outra entidade). **Duplicate não copia
     conexão nem sample data:** religue a conexão pelo `externalId` de `ap_list_connections` antes
     de validar, ou o flow passa na validação estrutural e falha em execução.
   - **Flow genuinamente novo → `ap_build_flow`**, que cria trigger e steps numa chamada só. Loop
     aninhado vai na mesma chamada, com `parentStepName` e `stepLocationRelativeToParent`.
   - **Editar flow existente → nunca reconstrua.** Use `ap_add_step`, `ap_update_step` e
     `ap_update_trigger`.

   **`ap_build_flow` não configura router.** Branch e condição não são configuráveis nessa chamada.
   Construa a espinha sem router, depois adicione cada router com `ap_add_step` e cada branch com
   `ap_add_branch` / `ap_update_branch`. Planeje o custo por isso: um flow com 9 routers e 11
   branches custa mais de 20 chamadas, não uma. Se a chamada recusar um branch, não repita — o
   caminho é o granular.

   **Antes de qualquer alteração estrutural num flow cujo spec já foi aprovado, releia a seção 7 do
   `spec.md`** (Integrações iPaaS) e as decisões fechadas já registradas no `changes.md`. Escolha de
   piece ou de step fechada no spec **não é negociável**: não troque por outra porque parece mais
   robusta, nem por hipótese de limitação que você não comprovou por leitura real. Se o spec
   genuinamente não cobrir o caso, **pergunte ao consultor** — nunca mude o caminho silenciosamente.
   Toda decisão fechada aqui vai para a coluna de decisões fechadas do `changes.md`, com piece,
   motivo e evidência: é o que faz a decisão sobreviver a timeout ou reconexão do connector, em vez
   de se perder com a conversa. **Aspas — dois lados, não confunda:** em **texto livre** (nome de
   step, mensagem, template, assunto, texto de payload) não envie `'` nem `"`, porque o transporte
   MCP não os carrega com confiabilidade: reescreva sem aspas e, se o valor só funcionar com elas,
   deixe aquele input como pendência manual da UI e registre o motivo no `changes.md`. Em
   **expressão/data pill** as aspas simples são **obrigatórias** — a forma canônica é
   `{{step_3['output']['data']['campo']}}` e não há alternativa aceita; remover as aspas produz
   expressão que não resolve. O **JavaScript de step de código** também é escrito com aspas
   normalmente. Nos dois casos, não escape, não troque por JSON e não repita a chamada para
   contornar.

   **Data pill nunca entra dentro de literal.** Não interpole `{{...}}` dentro de string JSON, de
   documento GraphQL montado como texto, nem de qualquer valor entre aspas. O motivo não é o texto
   que **você** escreve: é o valor que chega em runtime. Valor de campo do cliente pode conter
   `"`, `\` ou quebra de linha, e nesse instante a string que o envolve termina antes da hora
   — o payload fica inválido, ou pior, o conteúdo passa a ser interpretado como parte da consulta.
   É falha que a validação estrutural aprova e que só aparece com dado real. Ordem de escolha, e
   pare na primeira que servir: **(1) ação nativa da piece**, que recebe o valor como campo
   estruturado e não exige escape nenhum; **(2) variável de GraphQL**, com o valor fora do
   documento; **(3) nada**. Não existe terceira opção segura — montar a string "com cuidado" é a
   opção que já quebrou.
3. **Validar.** Rode a tool de validação do flow antes de qualquer teste ou publicação. Falha de
   validação deixa o item parcial; não publique. `ap_build_flow` ou `ap_validate_flow` aprovado
   comprova somente a configuração estrutural dos steps, não que uma expressão `{{...}}` resolve no
   payload runtime; use o estado de comprovação dos data pills para deixar isso explícito.
4. **Testar — obrigatório, não opcional.** **Nenhum flow é publicável sem uma run bem-sucedida.**
   Flow que só toca o Pipefy (ou webhook, schedule, código, tabelas) **deve** ser testado com
   `ap_test_flow`, ou `ap_test_step` quando você quiser isolar um step; não há razão para não
   testar, porque não há efeito externo. Teste que possa enviar mensagem, gravar em sistema externo,
   criar registro ou disparar webhook exige aprovação explícita para aquele teste e dados
   descartáveis — e, enquanto essa aprovação não vier, o flow **fica como rascunho**, não vai para
   publicação. Registre run id, entradas seguras, efeito esperado e resultado; não registre payloads
   sensíveis. Se o trigger não tiver sample salvo, passe `triggerTestData`.

   **O teste é o que converte `shape_unverified` em `shape_verified`.** A marca não é
   auto-declarada: ela significa **existe run com id e status de sucesso, e a saída dos steps
   confere com o que o spec esperava**. Sem run, tudo é `shape_unverified`, por definição — e a
   conferência checa isso por `ap_list_runs`, não pela sua palavra.

   **`valid: true` é falso verde.** Um flow inteiro pode reportar `valid: true` em todos os
   steps, passar em `ap_validate_flow` e ainda assim não funcionar: expressão que aponta para
   envelope errado, `inputs` que chega `undefined`, campo de mutation com nome errado, aspas que
   quebram um payload. Validação estrutural confere que os steps estão configurados, **nunca** que
   os dados atravessam. Já houve flow publicado com `valid: true` em todos os steps e quatro
   defeitos que uma única run teria exposto.
5. **Publicar.** Publicar/habilitar é uma aprovação separada da aprovação do spec e da aprovação de
   teste, e tem **pré-requisito**: run bem-sucedida registrada. Zero runs = não publica, mesmo com
   autorização de go-live e validação aprovada. Sem a autorização explícita de go-live, entregue o
   flow validado e testado como rascunho pronto para publicação. Após publicar, releia o flow ou
   estado de execução para confirmar o status ativo.

## Falhas, retomada e segurança

- `call_ipaas_tool` pode executar mesmo quando há timeout ou erro de transporte. Nunca repita a
  chamada às cegas: leia o flow, a lista de runs ou o run retornado antes de decidir a retomada.
- Aspas em **texto livre** (nome, mensagem, template, payload textual) têm comportamento não
  confiável via MCP e são proibidas: use formulação sem aspas ou entregue o input como pendência
  manual da UI. Aspas simples em **expressão/data pill** e em **JavaScript de step de código** são
  a forma normal e obrigatória — não as remova.
- Delete, retry, publish, enable e qualquer alteração em app externo exigem intenção explícita do
  consultor. Não use essas ações como tentativa de correção.
- **Reexecutar uma run é execução real e paga, e estratégias de retry não são mutuamente
  exclusivas.** Disparar duas para "ver qual funciona" processa o card duas vezes — aconteceu, com
  consultas pagas a bureaus externos em dobro. Uma estratégia por vez, resultado confirmado antes
  de considerar outra, e sempre com a intenção explícita do consultor.
- Se uma integração cruzar pipes, fixe no spec qual `pipe_id` é dono do flow e quais pipes apenas
  recebem efeito. Não deduza o alvo pelo nome.
- A conferência estrutural checa somente o flow e seus estados no iPaaS; comportamento em sistema
  externo é evidência de teste funcional, não suposição.

## Entrega

Para cada integração, informe: nome e objetivo, pipe dono, `flow_id`, conexão reutilizada (sem
segredo), situação dos data pills (`shape_verified` ou `shape_unverified`), status de validação,
evidência de teste quando houver, estado de publicação e qualquer pendência humana. Para conexão
ausente, informe o link de integrações do pipe; link direto do flow/workspace só é informado quando
a tool ou produto o retornar, nunca invente URL.
