# Schemas de Handoff — Pipefy Process Builder

Os artefatos abaixo são o canal entre as etapas. Como tudo roda no Claude Code, eles são
**arquivos numa pasta de trabalho** — não há pipe de controle nem card:

```
builds/<cliente>-<dominio>-<AAAA-MM-DD>/
  diagnostico.md      ← porta A (e início das portas C, D e E)
  spec.md             ← Planner        (portas B e C)
  agentes/<nome>.md    ← instrução completa de cada agente (Planner)
  emails/<nome>.html   ← corpo de template de e-mail quando longo (Planner/Builder)
  changes.md          ← Builder        (portas B e C)
  conferencia.md      ← Conferência    (portas B e C)
  roi-inputs.md       ← porta D, coleta (orquestrador)
  roi.md              ← porta D, cálculo (subagente)
  deck.md · deck.html · deck.pdf ← porta E
  test-results.md     ← Teste funcional (opcional, sob demanda)
  review.md           ← Review completo (opcional, sob demanda)
  snapshot-as-is.md   ← obrigatório na porta C, antes de qualquer escrita
  snapshot-final.md   ← só quando pedido
```

Cada etapa escreve exatamente o formato abaixo e lê **somente** os documentos de entrada da sua
etapa (matriz no fim). **Quais arquivos existem = onde o trabalho parou.**

Regra de escrita, válida para todos: frontmatter YAML obrigatório, seções na ordem fixa, tabelas
em vez de prosa, nada de narrativa sobre "como cheguei aqui". Documento completo, porém terso —
cada linha aqui será relida por outra etapa e reler custa dinheiro.

---

## 1. `spec.md` — escrito pelo Planner, lido por todas as etapas seguintes

```yaml
---
trabalho: <slug da pasta — ex.: acme-compras-2026-08-06>
porta: B | C
pipe_origem: <id + url | n/a>          # obrigatório na porta C
estrategia_aplicacao: direto | clone   # só na porta C
cliente: <nome>
org_destino: <nome + id>
workspace_destino: <nome + id | n/a>
dominio: <ex.: Compras>
aprovado_por: <solicitante>
aprovado_em: <YYYY-MM-DD>
versao: 1
---
```

**Resumo** (logo após o frontmatter, ≤5 linhas): objetivo + nº de fases + nº aproximado de campos +
automações + agentes de IA + integrações iPaaS.

### Seções (ordem fixa)
1. **Objetivo do processo** — 2 a 4 frases. O que o processo faz e para quem.
2. **Fases** — tabela: `# | Nome da fase | Objetivo | SLA | Responsável`.
3. **Campos por fase** — uma tabela por fase: `Campo | Tipo | Obrigatório | Preenchido por
   (Manual / Automação / Conector / Agente IA) | Condicional (se houver)`. **A primeira tabela é
   obrigatoriamente "Fase 0 — Start form"**, distinta da primeira fase visível: são objetos
   diferentes no Pipefy (o start form é uma fase oculta, `startFormPhaseId`), e um spec que os
   fundiu fez 36 campos nascerem na fase errada em 3 pipes. Campos que serão preenchidos **depois**
   por automação, agente ou iPaaS não podem ser obrigatórios no start form (bloqueiam a criação do
   card por e-mail e API).
4. **Automações** — tabela: `Nome (nomenclatura oficial) | Gatilho | Condição | Ação`. E-mail: cada
   automação `send_email_template` referencia uma linha da tabela **Templates de e-mail**
   (`Nome (nomenclatura oficial) | Assunto | Corpo (HTML, resumo ≤ 3 linhas + arquivo em
   emails/<nome>.html quando longo) | De (nome/e-mail) | Para | CC/BCC | locale/fuso | Entregabilidade
   (Nativo via create_email_template | Manual na UI)`). Não crie automação redundante para disparar
   agente cujo behavior já tem `card_created`.
5. **Condicionais** — tabela: `Nome | Fase de aplicação (onde estão os campos afetados) |
   Campo-gatilho | Regra (operação + valor) | Ação (esconder/mostrar quais campos, em que ramo)`.
   Nota: na plataforma, toda condicional é indexada sob a fase virtual Start form — a "fase de
   aplicação" do spec descreve onde a regra age (os campos das ações), não o atributo `phase`.
6. **Agentes de IA** — tabela: `Nome | Fase(s) | Gatilho (entrada na fase / campo select dedicado) |
   Tipo (AI 2.0 / +IDP / +Websearch) | Entradas | Saídas | Instrução (resumo ≤ 3 linhas + arquivo
   agentes/<nome>.md com o texto completo) | Observações de consumo`. A instrução completa é parte do
   spec: papel e objetivo, entradas nomeadas com id, critérios de decisão explícitos, saídas por campo
   com formato, exceções. Behavior sem gatilho discreto não é criável via API. Gatilho na **primeira
   fase** é `card_created`, nunca `card_moved`.
7. **Integrações iPaaS** — tabela: `Nome | Objetivo | Pipe dono (id) | Trigger | Steps/pieces |
   Entradas → saídas e procedência dos data pills (schema do pipe/piece/amostra) | Conexões requeridas
   (externalId reutilizado / a confirmar após criação) | Teste/e efeito externo | Estado esperado
   (rascunho / publicar após aprovação)`. Os **textos livres** de step (nome, mensagem, template)
   devem ser planejados sem aspas simples ou duplas; o que não puder ser reescrito assim é pendência
   manual da UI. Isso **não** vale para data pill: expressão se escreve na forma canônica
   `{{step_3['output']['data']['campo']}}`, com aspas simples. Se não houver integração:
   "Nenhuma". Não registrar credenciais, tokens nem URLs OAuth.
8. **Variações aplicadas** — decisões do decision_catalog escolhidas, e as recusadas relevantes.
9. **Entregabilidade** — tabela: `Item | Marca (Nativo / Contorno / Manual na UI / Integração) |
   Observação`. Classifica cada item do spec quanto ao que a ferramenta consegue entregar, para o
   solicitante aprovar sabendo o que vai sobrar de trabalho manual. Ver `connector-rules.md`, seção 4.
10. **Pendências manuais previstas** — o que ficará para configuração humana no Pipefy, com a
   **ligação das fases em primeiro lugar e em destaque** quando o build for de pipe novo: sem ela o
   processo não roda, por mais completa que a estrutura esteja.
11. **Open questions** — DEVE estar vazio. Spec com open question não é aprovável.

### Variante da porta C (deltas)
As seções 2 a 7 ganham a coluna `Operação (Adicionar / Alterar / Remover / Manter)`, referenciando
os ids do as-is que está no `diagnostico.md`. Itens `Remover` sobre estrutura com dados indicam a
alternativa aplicada (default: renomear com tag `[Inativo]`) ou a confirmação explícita do
solicitante para remoção real. O diagnóstico **não é copiado para cá** — ele já existe no
`diagnostico.md`; basta referenciar os achados aceitos.

---

## 2. `changes.md` — escrito pelo Builder, lido pela conferência (e pelo review)

```yaml
---
trabalho: <slug>
pipe_nome: <nome>
pipe_id: <id>
pipe_url: <link>
executado_em: <YYYY-MM-DD HH:MM>
spec_versao: <versão implementada>
status: COMPLETO | PARCIAL
---
```

**Resumo** (≤5 linhas): pipe + contagens (fases/campos/automações/agentes/integrações) + nº de desvios + nº de
pendências + totais lidos vs. esperados em toda listagem paginada ("automações: lidas 178 de 178").

### Seções (ordem fixa)
1. **Fases criadas** — tabela: `# | Nome | phase_id`. Confirmar remoção das fases default.
2. **Campos criados** — tabela por fase: `Campo | internal_id | Tipo`.
3. **Automações e condicionais** — tabela: `Nome | id | Status (criada e verificada / criada sem
   verificação / não criada — motivo)`. Linha adicional: `Templates de e-mail | id | criado via
   create_email_template e relido em get_email_templates | pendência manual (conteúdo em emails/)`.
4. **Agentes de IA** — tabela: `Nome | Status (configurado / parcial / manual pendente) | O que falta`.
5. **Integrações iPaaS** — tabela: `Nome | Pipe dono | flow_id | Decisões fechadas | Conexões
   reutilizadas (externalId) | Data pills (shape_verified / shape_unverified) | Validação estrutural |
   Teste (run_id/status ou não executado) | Publicação (rascunho/publicado/habilitado) | Status |
   O que falta`. **Decisões fechadas** registra, por flow, cada escolha de piece/step já decidida no
   formato `piece ou step escolhido (+ versão) | motivo | evidência (leitura do pipe, schema da piece
   ou run que comprovou)` — ex.: `getCardById v0.2.0 | devolve todos os campos do card indexados por slug (data.card.fields), sem
   custom_api_call | leitura do pipe`. A versão da piece entra porque envelope e inputs mudam entre
   versões, e um mesmo projeto costuma ter várias em uso ao mesmo tempo. Esta coluna existe porque a
   conversa não sobrevive a timeout ou reconexão do connector, e decisão perdida volta como
   retrabalho: o arquivo é a memória arquitetural do flow.
   Decisão registrada aqui não se reabre sem o consultor (ver `ipaas.md`, passo 2). Para conexão
   ausente, inclua piece, finalidade e o link `https://app.pipefy.com/pipes/<pipe_id>/integrations`.
   Não incluir segredo, token, URL OAuth ou payload sensível. **`shape_verified` exige run:** só
   marque assim o que tem run com id e status de sucesso cuja saída confere com o spec — sem run,
   a marca é `shape_unverified`, e flow com essa marca não é publicável.
6. **Desvios do spec** — diferença entre especificado e criado, com motivo. Se vazio: "Nenhum".
7. **Pendências manuais obrigatórias** — o que precisa ser feito na UI para o processo funcionar,
   **começando pela ligação das fases** (origem → destino, na ordem do fluxo), quando aplicável.
   Esta seção é a que o consultor vai executar à mão: escreva como instrução, não como aviso.
8. **Pendências / retomada** — se PARCIAL: o que falta e de onde retomar.
9. **Foco sugerido para o teste** — 3 a 5 pontos de menor confiança.

**Na porta C:** as seções 1 a 5 reportam por delta (`Operação | Item | id | Status`), incluindo os
`Manter` verificados como intactos. Registrar o mapeamento de cards feito antes das alterações e
cada remoção/inativação com a confirmação correspondente.

**Em clone-sandbox:** informar id/url do clone **e o resultado da verificação do original** — a
releitura do pipe de origem comparada ao snapshot dele. Escreva `original verificado e intocado` ou
a lista do que mudou lá, com ids. Não basta afirmar que o original não foi tocado: é preciso ter
verificado, porque já houve incidente de alteração caindo no original em vez do clone.

---

## 3. `conferencia.md` — escrito pela conferência, lido pelo orquestrador (e pelo review)

Formato completo em `03-conferencia.md`. Contrato mínimo:

```yaml
---
trabalho: <slug>
conferido_em: <YYYY-MM-DD HH:MM>
resultado: CONFORME | DIVERGENTE
divergencias: <número>
modo: completa | incremental
---
```

Seções: **Divergências** (tabela `# | Item | Esperado (spec) | Encontrado (pipe/iPaaS) | id` — só
divergências), **Pendências manuais na UI**, **Não verificável nesta etapa**, **Totais conferidos**.

---

## 4. `test-results.md` — opcional, escrito pelo teste funcional

Só existe quando o consultor pede o teste. **Não contém auditoria estrutural** — isso vive no
`conferencia.md` e repetir seria pagar duas vezes pela mesma verificação.

```yaml
---
trabalho: <slug>
testado_em: <YYYY-MM-DD HH:MM>
resultado: PASS | FAIL
card_de_teste: <id | n/a>
ipaas_runs: [<run_id | n/a>]
modo: completo | incremental
---
```

### Seções (ordem fixa)
1. **Casos executados** — tabela: `Caso | Ação | Resultado esperado | Resultado obtido | Status`.
   Para iPaaS, identificar o flow/run sem registrar dados sensíveis.
2. **Falhas** — onde (com id), o que ocorre, como reproduzir. Se vazio: "Nenhuma".
3. **Não testável** — o que só pode ser validado na UI (templates de e-mail, visual de
   condicional) ou o que não foi executado por risco de efeito externo em pipe vivo.
4. **Limpeza** — confirmação de que o card de teste foi excluído ou arquivado.

---

## 5. `review.md` — opcional, escrito pelo review completo

```yaml
---
trabalho: <slug>
revisado_em: <YYYY-MM-DD HH:MM>
veredito: SHIP | NEEDS WORK | BLOCK
ciclo: <nº>
---
```

### Seções (ordem fixa)
1. **Conformidade** — checklist com OK/FALHA + evidência: nomenclatura, best practices de
   modelagem, defaults de segurança.
2. **Coerência spec × construção × testes** — o pipe entrega o que o spec prometeu? Verde suspeito
   apontado.
3. **Correções exigidas** (obrigatória se NEEDS WORK) — tabela: `# | Onde (+ id) | O que corrigir |
   Referência`. Executável pelo Builder sem contexto adicional.
4. **Justificativa** (obrigatória se BLOCK).
5. **Recomendações não bloqueantes** — não impedem SHIP, não viram ciclo.

---

## 6. `diagnostico.md` — escrito pela porta A

Formato completo em `diagnostico.md` (o playbook). Contrato mínimo: frontmatter com `trabalho`,
`modo` (pipe | documentacao), `cliente`, `pipe_analisado`, `dominio`, `diagnosticado_em`,
`defeitos`; seções **Resumo executivo**,
**Defeitos encontrados** (ou **Lacunas**, no modo documentação; inclui também **Integrações iPaaS**
— flows, estado, runs — e **Lint estrutural**, ver `diagnostico.md`, passo 2.5), **Conformidade**,
**Alinhamento à BU**, **Oportunidades** e **As-is** (só modo pipe). Toda contagem declara "lidos N
de N".

A seção **As-is** é o que permite a porta C montar deltas sem reler o pipe — ela tem que trazer
ids reais.

---

## 7. Snapshots — formato compacto (`snapshot-as-is.md`, `snapshot-final.md`)

Snapshot é seguro de rollback e retrato as-built. **Não é dump de JSON.** Fazer o modelo ler o JSON
completo do pipe e reescrevê-lo é a operação mais cara do fluxo inteiro (dezenas de milhares de
output tokens) e não melhora o rollback em nada.

Formato: frontmatter (`trabalho`, `pipe_id`, `pipe_url`, `capturado_em`, `tipo: as-is | final`)
seguido das mesmas tabelas das seções 2 a 6 do spec, com **ids reais** em cada linha — fases com
phase_id, campos com internal_id, automações e condicionais com id, agentes com id. Uma leitura
(`graphql-recipes.md`, seção 1) alimenta tudo isso.

- `snapshot-as-is.md` — **obrigatório** na porta C, antes de qualquer escrita. Se o
  `diagnostico.md` da mesma sessão já traz o As-is com ids, ele serve: registre isso no changes.
  **Em clone-sandbox, o snapshot é do pipe original** (o que precisa ficar intocado) — é ele que
  permite verificar no fim se alguma escrita escapou para lá.
- `snapshot-final.md` — **só quando pedido**. Serve de registro para consulta futura do próprio
  consultor; não é requisito de entrega.

---

## 8. `roi-inputs.md` — escrito pelo orquestrador (porta D), lido pelo subagente de cálculo

```yaml
---
trabalho: <slug>
cliente: <nome>
pipe_analisado: <id + url>
modo: realizado | projetado
periodo_inicio: <YYYY-MM-DD>
periodo_fim: <YYYY-MM-DD>
moeda_base: BRL
cambio_usd_brl: <valor informado | n/a>      # com data e quem informou, na seção 4
coletado_em: <YYYY-MM-DD>
---
```
1. **Investimento** — tabela: `Item | Valor | Moeda | Recorrente? (sim/não, periodicidade) | Origem
   (quem informou / documento)`. Ex.: licença, horas de Professional Services, custos de integração.
2. **Benefício** — tabela: `Tipo (economia de custo / ganho de produtividade / aumento de receita /
   horas-FTE economizadas) | Quantidade | Unidade | Período | Origem | Conversão financeira (custo
   FTE informado ou "não convertível")`. Horas sem custo FTE informado ficam como horas.
3. **Métricas lidas do pipe** — tabela: `Métrica | Valor | Fonte (query/tool) | Limitação`. Ex.:
   cards criados no período, execuções por automação (avaliadas, não executadas), runs iPaaS, tempo
   médio por fase na amostra de N cards, cards atrasados.
4. **Premissas explicitamente informadas** — uma por linha, com quem informou e quando.
5. **Lacunas** — o que faltou para um cálculo confiável e quem responde.

---

## 9. `roi.md` — escrito pelo subagente de cálculo (porta D), lido pelo orquestrador e pela porta E

```yaml
---
trabalho: <slug>
cliente: <nome>
modo: realizado | projetado
periodo: <início a fim>
moeda: BRL
status: calculado | nao_calculavel
fonte_inputs: roi-inputs.md
calculado_em: <YYYY-MM-DD HH:MM>
---
```
Seções na ordem fixa do prompt de cálculo (`references/roi.md`): 1. **Dados utilizados** (com
origem de cada valor) · 2. **Premissas** (somente as explicitamente informadas) · 3. **Cálculo**
(fórmula com valores substituídos) · 4. **Resultado** (investimento total, benefício financeiro,
retorno líquido, ROI %, payback em meses) · 5. **Validação** (checagem independente) · 6. **Alertas**
(limitações, dados faltantes, arredondamentos, inconsistências). Se `status: nao_calculavel`, a
seção 4 traz só a frase "ROI não calculável com segurança" e a 6 lista o que falta.

---

## 10. `deck.md` — escrito pelo subagente de redação (porta E), completado pelo orquestrador

```yaml
---
trabalho: <slug>
cliente: <nome>
base: diagnostico | diagnostico+roi
gerado_em: <YYYY-MM-DD HH:MM>
arquivos: [deck.html, deck.pdf]
drive_link: <url | n/a>
kit_de_marca: provisorio | oficial
---
```
1. **Roteiro** — tabela: `# | Slide | Fonte (arquivo e seção) | Números usados`.
2. **QA** — checklist com resultado: PDF com camada de texto; todo número do deck existe em
   `diagnostico.md`/`roi.md`; nenhum rótulo com `[`/`]` quebrando diagrama; nenhum segredo, token ou
   dado pessoal; modo do ROI rotulado.
3. **Pendências** — o que o consultor revisa antes de apresentar.

---

## Matriz de leitura (quem lê o quê)

| Etapa | Lê | Escreve |
|---|---|---|
| Diagnóstico (porta A) | pipe via `AuditPipe` + automações e agentes paginados + flows iPaaS quando houver (3 a 6 chamadas) + `golden_standard_schema.md`/`decision_catalog.md` + documentos do cliente | `diagnostico.md` |
| Planner | `golden_standard_schema.md`/`decision_catalog.md` + conversa com o solicitante + `diagnostico.md` (porta C) | `spec.md` |
| Builder | `spec.md` (+ divergências da `conferencia.md` ou correções do `review.md`) | pipe do cliente + `changes.md` (+ `snapshot-as-is.md` na porta C) |
| Conferência | `spec.md` + `changes.md` + 1 leitura do pipe + leitura iPaaS quando houver integração | `conferencia.md` |
| Teste funcional (opcional) | `spec.md` + `changes.md` + `conferencia.md` | card de teste (temporário) + runs iPaaS aprovados + `test-results.md` |
| Review completo (opcional) | `spec.md` + `changes.md` + `conferencia.md` + `test-results.md` + 1 leitura do pipe | `review.md` (+ `snapshot-final.md` se pedido) |
| Porta D — coleta (orquestrador) | `diagnostico.md` + métricas do pipe (`graphql-recipes.md` §8.5–8.7, somente leitura) + respostas do consultor | `roi-inputs.md` |
| Porta D — cálculo (subagente) | `roi-inputs.md` + `diagnostico.md` | `roi.md` |
| Porta E — redação (subagente) | `diagnostico.md` (+ `roi.md`) + `references/deck-template.html` | `deck.md`, `deck.html` |
| Porta E — geração e QA (orquestrador) | `deck.html`, `deck.md` | `deck.pdf` (+ link do Drive) |

Ninguém lê a conversa de outra etapa. Ninguém relê o pipe fase por fase.
