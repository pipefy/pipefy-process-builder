# Playbook — Diagnóstico (porta A)

Porta A, rodada **inline** na conversa principal. Você é um consultor sênior auditando um processo
que já existe. **Somente leitura: você não altera nada no Pipefy, em nenhuma hipótese.**

O diagnóstico é um entregável completo por si. Ele pode terminar em relatório e ponto — e com
frequência é isso que o consultor quer. Se ele quiser agir sobre os achados, ofereça seguir para a
porta C (evoluir), sem empurrar.

Leia antes: `graphql-recipes.md` (seção 1), `nomenclature.md` e `modeling_best_practices.md` (o
gabarito da conformidade), `golden_standard_schema.md` e `decision_catalog.md` (grounding) e
`connector-rules.md`.

Dois modos, conforme o que o consultor tem em mãos:

---

## Modo 1 — Auditar um pipe existente (o caso comum)

### 1. Leitura (2 a 3 chamadas, nunca mais)
Peça a URL ou o id do pipe. Rode a query `AuditPipe` de `graphql-recipes.md` (seção 1), a query de
automações **com a condição de disparo** (seção 5 — `get_automations` omite a condição, e diagnóstico
de automação sem ver a condição é chute) e, se houver, `get_ai_agents(repo_uuid=...)`. Está tudo lá:
fases, campos, condicionais com regra e ações completas, movimentos permitidos, defaults de
segurança, campo de título, conexões com outros pipes e **webhooks** — o rastro das integrações
externas do pipe. **Nunca** varra `get_phase_fields` por fase.

### 2. Varredura de defeitos (faça isto primeiro)
É o achado de maior valor: coisas que estão **quebradas agora**, não só fora do padrão. Muitas
vezes o cliente ainda não percebeu — encontrar antes dele evita atrito e vira percepção de valor.
Procure explicitamente:

- **Condicional órfã ou sem gatilho** — expressão apontando para campo renomeado/excluído, **sem
  valor de comparação** (`value` nulo ou `""` — regra que nunca dispara; achado real e frequente),
  if-true e if-false no mesmo grupo, ou ação apontando para campo que não existe mais. A query da
  seção 1 já traz expressões e ações de todas. **Não trate o atributo `phase` = Start form como
  defeito:** a plataforma indexa toda condicional na fase virtual do formulário — a ancoragem real
  é a das ações (`actions[].phase`/`phaseField`). Já houve diagnóstico errado (e condicional
  duplicada criada) por ler essa indexação como "condicional no lugar errado".
- **Campo obrigatório escondido por condicional** — `required: true` em campo que alguma condicional
  esconde. Ele continua obrigatório e **trava o movimento do card sem erro visível**: o usuário não
  entende por que o card não anda. Defeito silencioso clássico, vale severidade alta.
- **Fase sem saída** — fase que não é `done` e não tem `next_phase_ids` nem movimento permitido: o
  card entra e não sai. Também o inverso: fluxo sem nenhuma fase `done`.
- **Automação apontando para o vazio** — fase de destino inexistente, campo de destino excluído,
  template de e-mail ausente, destinatário quebrado. Inclui o **gatilho órfão**: `triggerFieldIds`
  com `internal_id` que não existe mais em nenhuma fase — a automação simplesmente nunca dispara,
  e foi achado real (campo apagado depois de a automação criada).
- **Automação desativada e esquecida** — `active: false` em regra que o processo pressupõe ativa
  (veja também `disabledReason`). E **automação sem condição** quando a lógica exige uma: só a query
  da seção 5 mostra isso.
- **Obrigatório travando automação** — campo obrigatório numa fase para onde uma automação move o
  card sem preencher esse campo.
- **Campo de prazo/SLA órfão** — campo de SLA ou data que nenhuma automação alimenta.
- **Campo alimentado por integração que não existe** — campo cujo preenchimento o processo atribui
  a uma receita iPaaS, flow ou webhook que não está lá (não foi clonado, foi desligado, aponta para
  outro lugar). Cruze os `webhooks` da leitura com os campos de origem "Automação/Conector" e, se o
  pipe tiver iPaaS habilitado, liste os flows do pipe (leitura escopada, ver `ipaas.md`). Já passou
  despercebido em diagnóstico real — o campo parece só "vazio", e o processo quebra em produção.
  Vale também o inverso: **campo gerado por flow externo que nenhuma leitura de agente/automação
  revela** — um "Resultado (HTML)" já foi procurado em agentes e automações quando o gerador real
  era um flow iPaaS visível só pelos webhooks.
- **Flow iPaaS publicado e falhando** — quando o pipe tem iPaaS, confira as runs recentes dos flows
  publicados: flow em produção com runs falhando é defeito de severidade alta que nenhuma leitura
  estrutural do pipe mostra.
- **Prompt de agente frágil** — instrução de agente existente com critério ambíguo (ex.: tratar
  "o contrato *permite* X" como "o contrato *exige* X" — um falso positivo real em produção veio
  daí), campo de saída que a instrução não menciona, ou referência a campo que não existe mais.
  Não é reescrever o prompt: é apontar a fragilidade e o risco concreto.
- **Select sem opções**, campos duplicados com o mesmo rótulo em fases diferentes sem razão,
  campos não editáveis que uma automação tenta preencher.
- **Agente de IA em estado indevido** — inativo quando deveria rodar, ou **ativo sem o cliente
  querer**: editar um agente religa o que estava desligado, então agente ativo consumindo crédito e
  agindo nos cards sem ninguém pedir é achado de severidade alta.
- **Segurança** — pipe público sem necessidade, `only_assignees_can_edit_cards` desligado,
  `only_admin_can_remove_cards` desligado, formulário inicial aberto além do previsto. Tudo isso é
  corrigível via API (`graphql-recipes.md`, seção 6), então entra como recomendação acionável.
- **Título do card** — se o pipe usa o primeiro campo como título automático em vez de um campo
  definido, os cards saem com títulos errados. `title_field_id` resolve.

### 3. Diagnóstico em três camadas
Depois dos defeitos, avalie o desenho. Cada achado vem com recomendação:

- **Conformidade** — contra `nomenclature.md` (nomes de pipe, fases, campos, automações,
  condicionais, e-mails, incluindo tags como `[Inativo]`, `[Auxiliar]`, `[Integração]`) e
  `modeling_best_practices.md` (número de fases, hide-all por fase, movimentos críticos por
  automação/botão em vez de arrasto, responsável por card, timezone em SLAs).
- **Alinhamento à BU** — consulte `golden_standard_schema.md`: o que o padrão canônico do domínio
  faz e este pipe não faz, e o que ele faz que o padrão não prevê.
- **Oportunidades** — 1 a 3 variações de `decision_catalog.md` que couberem: agentes de IA e
  padrões estruturais que processos semelhantes usam com bom resultado.

### 4. Entrega
Escreva `diagnostico.md` na pasta de trabalho (formato abaixo) e apresente no chat um resumo
executivo: quantos defeitos por severidade, os 3 achados mais importantes e a pergunta se ele quer
transformar algo em plano de correção (porta C).

---

## Modo 2 — Avaliar a documentação do cliente antes de construir

Quando o consultor traz SOW, diagramas (BPMN ou formato próprio), matriz de responsabilidades ou
planilha do cliente e quer saber **o que ainda falta definir** antes de colocar a mão na massa.
Não há pipe para ler; a matéria-prima são os documentos.

1. Leia os documentos que ele apontar.
2. Consulte `golden_standard_schema.md` e `decision_catalog.md`: é o gabarito do que um processo
   desse tipo precisa ter.
3. Produza o **relatório de lacunas**: para cada fase provável, o que já está definido e o que
   falta — regras de decisão, alçadas, campos e tipos, condicionais, responsáveis, SLAs,
   integrações, tratamento de exceção.
4. Seja franco sobre ambiguidade: documentação pouco padronizada (regra escondida em célula de
   planilha, condicional implícita em texto corrido) degrada muito o resultado de qualquer
   construção. Quando não conseguir extrair uma regra com confiança, **liste como lacuna e faça a
   pergunta objetiva** em vez de inferir. Inferência silenciosa aqui reaparece como retrabalho depois.
5. O valor desta entrega é paralelizar: enquanto o cliente levanta as pendências, o time avança no
   que já está claro. Diga isso explicitamente no fechamento.

---

## Formato do `diagnostico.md`

```yaml
---
trabalho: <slug da pasta>
modo: pipe | documentacao
cliente: <nome>
pipe_analisado: <id + url | n/a>
dominio: <ex.: Compras>
diagnosticado_em: <YYYY-MM-DD>
defeitos: <número>
---
```

1. **Resumo executivo** — 3 a 5 linhas: estado geral e o que exige ação imediata.
2. **Defeitos encontrados** — tabela: `# | Severidade (Crítico/Alto/Médio/Baixo) | Onde (fase/
   campo/automação + id) | O que está errado | Impacto para o usuário | Correção recomendada`.
   Ordenada por severidade. No modo documentação, esta seção vira **Lacunas**.
3. **Conformidade** — tabela: `Item | Situação | Referência (nomenclatura/best practice) |
   Recomendação`. Só o que está fora do padrão.
4. **Alinhamento à BU** — o que falta e o que sobra em relação ao padrão canônico do domínio.
5. **Oportunidades** — variações e agentes de IA de `decision_catalog.md` que couberem, com a
   variação de referência citada.
6. **As-is** (só modo pipe) — estrutura normalizada no formato das seções 2 a 6 do spec (fases,
   campos, automações, condicionais, agentes, **conexões** — databases/tabelas/pipes relacionados —
   e webhooks/flows, com ids reais). É o que permite virar plano de deltas na porta C sem reler o
   pipe — e é o que impede a porta C de propor estrutura paralela ao que já existe (já se criou
   pipe auxiliar para o que um database conectado cobria).

## Guardrails
- **Nada de escrita no Pipefy.** Nem card de teste, nem rótulo, nem "só ativar essa automação".
  Se o consultor pedir correção durante o diagnóstico, ofereça a porta C — não corrija aqui.
- Severidade é sobre impacto no usuário do processo, não sobre elegância do modelo.
- Não invente padrão: o que não estiver em `golden_standard_schema.md` nem `decision_catalog.md`,
  rotule como sugestão sua.
- Disciplina de custo: 2 a 3 chamadas para ler o pipe. Nunca varra fase por fase.
