# Decision Catalog — Patterns and AI-Agent Opportunities to Offer

This supports step 4 of the build: the consultative conversation. It lists the native-AI-agent
opportunities to push for and the optional structural patterns to offer. Offer these as professional
recommendations in the user's language — you may note lightly that something is common or recommended
for this kind of process, but do not keep citing the reference library or naming a base. Only raise a
pattern whose preconditions fit the process, and ask a few at a time.

Maintain this file as the library grows: as new processes are added, fold their decision points and
AI opportunities into the entries here. Keep the offer questions in Portuguese by default.

---

## Native AI agents — recommend aggressively

Putting native Pipefy AI agents into the process is a priority, and this is the most valuable part of
the consultation. Scan the whole flow and proactively recommend a native AI agent wherever it
genuinely helps; default toward including them and have the user opt out, rather than waiting to be
asked. Discover at runtime what native AI-agent configuration the Pipefy connector supports; configure
what you can and flag anything that needs manual setup.

Common insertion points:
- **Document/quote validation** — validate supplier quotes or attached documents and flag issues.
- **Compliance checking** — check a request against rules and produce a pass/fail with a summary.
- **Data extraction** — pull structured fields out of attachments (quotes, invoices, contracts).
- **Classification / triage** — categorize or route a request (urgent, spot buy, amendment, etc.).
- **Summarization** — summarize a card's history or the supplier responses for the operator.
- **Drafting** — draft messages or responses for the operator to review.

Where a reference process achieved one of these through an external connector, propose realizing the
same intent with a native Pipefy AI agent instead.

Follow `modeling_best_practices.md` (Pipefy AI): prefer AI 2.0 agents; use AI + IDP when documents must
be read (PDF/PNG/JPEG, complex or standardized tables) and AI + Websearch when the process needs
real-time external data (e.g., FX rates). Tell the client these raise consumption, and validate
Websearch use with the AI team.

When you settle an agent with the user, settle its **trigger** too — the card entering a phase, or a
dedicated select field (production pattern: "Iniciar análise com IA" = Sim). Behaviors without a
discrete trigger cannot be created via the API, and a trigger discovered mid-build becomes an
unplanned field. Agents are always built in the Agents tab (`create_ai_agent`), never as automations
with an "ask AI" action. These offers apply to porta C evolutions as much as to new builds — an
existing pipe with no agents is exactly where the recommendation is most valuable.

Example offer:
> Recomendo colocar um agente de IA nativo do Pipefy para validar as cotações automaticamente e
> sinalizar divergências, em vez de conferência manual — posso já incluir. Quer também um agente para
> checar compliance e gerar um resumo de aprovado/reprovado?

---

## Structural patterns

Each entry gives: what it is, when to offer it, the question to ask, the typical configuration, and a
build note.

### 1. Data entry: system-fed vs manual start form
- **What it is:** Whether requests are created manually via a start form or pushed automatically from
  an external system (e.g., SAP/ERP) via API, in which case there is no start form.
- **When to offer:** Always, at the start.
- **Offer:** "As requisições vão entrar manualmente por um formulário, ou vão ser criadas
  automaticamente por um sistema externo (ex.: ERP/SAP) via integração?"
- **Typical config:** System-fed → no start form; initial fields mapped via integration. Manual → a
  start form with the requester's fields.
- **Build note:** If system-fed, omit the start form and coordinate field mapping with integration.

### 2. Parallel pipes vs single pipe
- **What it is:** Running the same flow as two or more parallel pipes (e.g., for region, client, or
  complexity), with cross-pipe routing automations; vs a single pipe.
- **When to offer:** When the process has clear variants.
- **Offer:** "Esse processo tem mais de uma variante (por região, cliente ou complexidade) que
  justifica pipes paralelos com roteamento entre eles, ou um único pipe cobre tudo?"
- **Typical config:** A fuller pipe and a lighter pipe sharing the same phases, with routing
  automations moving cards to the matching phase in the other pipe.
- **Build note:** Heavy — build each pipe and the cross-pipe routing carefully and verify the routing.

### 3. SLA tracking granularity
- **What it is:** End-to-end SLA plus per-phase timing on every phase, vs a single global deadline.
- **When to offer:** When the operation tracks performance per phase.
- **Offer:** "Você quer medir o tempo em cada fase individualmente (SLA por fase + tempo decorrido),
  além do SLA ponta a ponta, ou basta um prazo global?"
- **Typical config:** An end-to-end SLA (due-date) plus time-in-phase and elapsed-time (number) on each
  phase.
- **Build note:** Adds three automated fields per phase.

### 4. AHT (Average Handling Time) measurement
- **What it is:** Measuring effective handling time per activity category with in/out timestamps and
  total-time calculations in the closing phase.
- **When to offer:** When the operation needs operator-level efficiency metrics.
- **Offer:** "A operação precisa medir o tempo efetivo de manuseio por categoria de atividade (AHT),
  ou o SLA ponta a ponta já é suficiente?"
- **Typical config:** In/out timestamp fields per category, plus last-stop, stopped-total, and total
  AHT fields in the closing phase.
- **Build note:** Adds several automated datetime/number fields in the final phase.

### 5. Quote validation by native AI agent
- **What it is:** A native Pipefy AI agent that validates supplier quotes and flags divergences. In the
  reference processes this was done through an external connector; prefer a native AI agent.
- **When to offer:** Whenever the process receives quotes. Recommend it.
- **Offer:** "Recomendo um agente de IA nativo para validar as cotações automaticamente e sinalizar
  divergências, em vez de conferência manual. Posso incluir?"
- **Typical config:** A native AI agent acting where quotes are reviewed, producing a status and notes.
- **Build note:** Configure as a native AI agent on the relevant phases; flag manual setup if the
  connector cannot fully configure it.

### 6. Compliance validation by native AI agent
- **What it is:** A native Pipefy AI agent that checks a request against compliance rules and produces a
  pass/fail with a summary. Done via an external connector in the references; prefer a native AI agent.
- **When to offer:** In compliance-sensitive processes. Recommend it.
- **Offer:** "Recomendo um agente de IA nativo para checar compliance e gerar um resumo de
  aprovado/reprovado automaticamente. Quer incluir?"
- **Typical config:** A native AI agent producing a compliance summary and a pass/fail signal.
- **Build note:** Configure as a native AI agent; flag manual setup if the connector cannot fully
  configure it.

### 7. Block/hold phases (Client hold / Supplier hold)
- **What it is:** Dedicated phases for blocks caused by the client side or the supplier side, each with
  reason fields and a "pending with" field; optionally a scheduled follow-up.
- **When to offer:** Whenever a request can be blocked by an external party.
- **Offer:** "O processo pode travar por pendência do cliente ou do fornecedor? Se sim, crio fases de
  bloqueio com motivo e responsável — e você quer também um campo de follow-up agendado nessas fases?"
- **Typical config:** Client-hold and supplier-hold phases with reason and "pending with" fields;
  optional "next follow-up scheduled on" (due-date).
- **Build note:** Follow-up scheduling is its own sub-toggle.

### 8. System / technical phase (high volume)
- **What it is:** A dedicated phase for administrative and bulk operations (bulk move, SLA adjustment,
  card status), used by operators and admins; not a business step.
- **When to offer:** For high-volume operations (hundreds of cards/day).
- **Offer:** "O volume de cards é alto a ponto de justificar uma fase técnica de operações em massa
  (bulk move, ajuste de SLA), ou as ações administrativas podem ser feitas direto nas fases?"
- **Typical config:** A system phase with bulk-move checklist, move-to-phase select, and SLA/status
  fields.
- **Build note:** Recommend only for high volume.

### 9. Hierarchical classification (L1/L2)
- **What it is:** Classifying transactions into two hierarchical levels for BI/reporting.
- **When to offer:** When clean reporting data matters.
- **Offer:** "Você precisa classificar as transações em níveis hierárquicos (L1/L2) para reporting/BI,
  ou uma classificação simples basta?"
- **Typical config:** Two classification selects near the end of the flow.
- **Build note:** Lightweight.

### 10. Approval threshold
- **What it is:** Above a monetary threshold (e.g., R$ X), a card requires direct approval from the
  leader before proceeding. Note: pure-execution BPO flows often have no approval step, so this comes
  from other processes — offer it where appropriate.
- **When to offer:** When the client wants spend control / leader sign-off.
- **Offer:** "Para aprovação, você quer (a) incluir uma aprovação direta do líder para compras acima de
  um valor — ex.: R$ X —, (b) usar outro valor de limite, ou (c) seguir sem etapa de aprovação?"
- **Typical config:** An approval phase or gate keyed to a value field, routing high-value cards to the
  leader before continuing.
- **Build note:** Model the threshold as a field/condition and add the approval step.

### 11. Spot-buy branch
- **What it is:** A dedicated phase for one-off, off-contract purchases without the standard
  competitive process.
- **When to offer:** Common in procurement.
- **Offer:** "O processo trata compras pontuais fora de contrato (spot buy) com tratamento próprio, ou
  todas as compras seguem o mesmo fluxo?"
- **Typical config:** A spot-buy phase with category and bid-classification fields.
- **Build note:** Adds one branch phase.

### 12. PR amendment branch
- **What it is:** Handling requests that need changes (price, quantity, data), with change tracking and
  "line vs header" differentiation.
- **When to offer:** Common in procurement.
- **Offer:** "Requisições vão poder ser alteradas (preço, quantidade, dados) e precisam de rastreamento
  dessas mudanças, ou alterações não fazem parte do escopo?"
- **Typical config:** An amendment phase with amendment-type fields and change tracking (or simple
  price/quantity-change labels in lighter variants).
- **Build note:** Build the change-tracking fields/connectors and verify they capture the change type.

### 13. Supplier management phase
- **What it is:** Handling supplier onboarding, enablement, or qualification.
- **When to offer:** When supplier setup is part of the flow.
- **Offer:** "O processo precisa tratar cadastro/qualificação de fornecedor numa fase própria, ou isso
  fica fora do escopo?"
- **Typical config:** A supplier-management phase with classification and awarded-supplier fields.
- **Build note:** Adds one phase.

### 14. Non-compliant handling phase
- **What it is:** A dedicated phase for requests that fail the compliance check and need specific
  treatment before continuing or closing.
- **When to offer:** Pairs with compliance validation.
- **Offer:** "Requisições que reprovarem no compliance devem ir para uma fase de tratamento dedicada,
  ou são apenas encerradas?"
- **Typical config:** A non-compliant phase with compliance-class and classification fields.
- **Build note:** Adds one branch phase.

### 15. Porta B → Porta C (conectar o pipe novo a um pipe existente)
- **What it is:** During a new build, the design needs a relation, connector field or automation
  touching a pipe that already runs (handoff, parent/child, lookup).
- **When to offer:** As soon as the spec references an existing pipe id.
- **Offer:** "O processo novo vai se conectar ao pipe <nome/id> que já está em produção. Isso muda a
  escrita para um pipe vivo: quer que eu inclua essa conexão agora (com relação pai/filho e os flags
  `canCreateNewItems` explícitos), ou deixo como pendência para uma rodada de evolução?"
- **Typical config:** `create_pipe_relation` + `update_pipe_relation` (three flags) before any
  `create_connected_card` automation; the existing pipe is declared as a second target id.
- **Build note:** Approval is explicit and recorded in the spec; the protocol of
  `connector-rules.md` §5 applies (two pipes in session).

### 16. Template de e-mail: nativo via perk ou manual
- **What it is:** Whether e-mail templates can be created in this session.
- **When to offer:** Whenever the process sends e-mail.
- **Offer:** With `create_email_template` present: "Crio os templates direto no pipe, em pt-BR e fuso
  America/Sao_Paulo quando o processo for brasileiro (país da pergunta 0), e ligo as automações de
  envio." Without it: "Deixo assunto e corpo prontos para
  colar e ligo o envio quando o template existir — ou instalamos o perk local antes do build."
- **Build note:** See `connector-rules.md` §4.11.

### 17. Padrão mínimo de instrução de agente
- **What it is:** The agent instruction text is part of the spec, not a build-time improvisation.
- **When to offer:** Whenever an AI agent is settled.
- **Offer:** "Vou escrever a instrução completa do agente no spec (papel, entradas com id, critérios,
  saídas por campo, exceções) para você revisar antes do build."
- **Build note:** Two-line prompts generated "from context" were rewritten by hand in a real build;
  the Builder copies the spec text verbatim (≤ 10.000 characters).
