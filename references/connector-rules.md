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
| **Ligar as fases umas às outras** | `cards_can_be_moved_to_phases` **não tem mutation** (verificado em `UpdatePhaseInput`, `SettingsInput` e na lista completa de mutations). Só a aba "Fluxo" da UI configura |
| Descrição do pipe | Não existe em `UpdatePipeInput` |
| Template de e-mail | Só criar/ler/enviar; **sem update e sem delete** |
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

- **Segurança do pipe e campo de título:** a tool `update_pipe` aceita só nome/ícone/cor, mas a API
  aceita `public`, `public_form`, `only_assignees_can_edit_cards`, `only_admin_can_remove_cards` e
  `title_field_id` — ver `graphql-recipes.md`, seção 6. **Não é pendência manual.**
- **Condição de disparo da automação:** `get_automations` omite o campo `condition`. A query da
  seção 5 de `graphql-recipes.md` traz. Isso já causou reprovação indevida de um build inteiro.
- **Lote de valores de campo de card:** existe `updateFieldsValues` — seção 7 de `graphql-recipes.md`.

### 4.3 Armadilhas de escrita — verifique **depois** de escrever

- **Condicional fantasma (o pior deles).** `create_field_condition` pode responder "criado com
  sucesso" e a regra **não persistir**, ou ser gravada **na fase errada** (tipicamente no
  formulário inicial). Observado em 5 builds. Depois de criar qualquer condicional, releia e
  confirme que ela existe **e está na fase certa** antes de reportar como pronta. Um "sucesso"
  mentiroso engana você e quem confia no seu relatório.
- **Condicional sem valor de comparação.** O `value` da condição fica nulo e a regra nunca dispara.
  Preencha sempre o valor de comparação e confirme na releitura.
- **Agente de IA nasce ativo, e editar religa.** Todo agente criado nasce ativo, e um `update` zera
  o `disabledAt` — ou seja, **um agente que o cliente havia desligado volta a rodar**, gastando
  crédito de IA e agindo nos cards sem ninguém pedir. Se o spec não pede o agente ativo, desative
  logo após criar (`toggle_ai_agent_status`). Na porta C, **registre o estado de cada agente antes
  de editar e restaure depois**.
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
- `delete_phase_field` exige o **uuid do pipe**, não só o id do campo.
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
- Depois de timeout/erro em `call_ipaas_tool`, não repita. A ação pode já ter executado; confira flow,
  lista de runs ou run específico e registre a retomada.
- **Expressão sem procedência (data pill no escuro).** Não escreva `{{trigger...}}` ou
  `{{step_...}}` por analogia com outro webhook/piece. Para cada expressão, registre a evidência do
  path: schema real do pipe, schema/documentação da piece/action ou amostra segura. Schema de campo
  Pipefy não prova sozinho o envelope do trigger. Sem path comprovado, marque `shape_unverified`,
  peça autorização para teste controlado se necessário e não publique o flow. Validação estrutural
  não elimina essa pendência.
- Conexão ausente bloqueia somente o trecho dependente, não o restante do build. Registre piece,
  finalidade e o link `https://app.pipefy.com/pipes/<pipe_id>/integrations`; não crie um mock que
  pareça flow funcional nem tente criar/rotacionar a conexão.
- Validar rascunho não autoriza teste externo, nem comprova data pills. Testar externamente não
  autoriza publicar. Publicar ou habilitar sem aprovação explícita é mudança indevida. Veja
  `ipaas.md` para o ciclo completo.

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
