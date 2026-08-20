# Golden-Standard Document — Schema (Parse Contract)

Every golden-standard process document in the library follows this fixed structure, produced upstream
by a templated documenter. Only the content changes between documents. The documents are written in
Portuguese. Use this contract to parse a document reliably and to know where each piece of
information lives.

## Frontmatter (metadata)
A short header block with: `caso_de_uso` (process name), `cliente`, `industria`, `maturidade`
(maturity level), `tags`, source identifiers (e.g., `pipe_id`), and `gerado_em` (generated date).
Use this to match a requested process to the closest base (by domain, industry, and maturity).

## 1. Visão Geral do Processo (Process Overview)
Narrative of what the process does end to end, plus a **structural summary**: number of phases,
approximate field counts, number of automation groups, whether AI agents are present, and which
external/internal connectors are used. This is the fastest way to size a process and spot whether it
uses parallel pipes, AI validators, or external integrations.

## 2. Formulário de Entrada (Start Form)
Whether the process has a manual start form or is fed by an external system via API (e.g., SAP
S4HANA). If API-fed, there is no start form and the initial fields are mapped via integration. This
is the first variation point (see the decision catalog).

## 3. Fases e Campos (Phases & Fields)
The core. For each phase: an objective, then a **table of fields**. Each field row gives: field name,
type (`select`, `short_text`, `long_text`, `number`, `date`/`due_date`, `radio_*`, `label_select`,
`checklist_*`, `attachment`, `connector`, `assignee_select`, `datetime`), whether it is required,
and who fills it (Manual, Automação/API, Conector interno, or Agente IA). When the process uses
parallel pipes (e.g., CH and CL), the document shows the richer pipe's fields and notes how the
lighter pipe differs.

Parse this section to build the phase order, the per-phase field list, and the source of each field
(which fields are user-filled vs automated vs connector/AI-driven).

## 4. Automações Configuradas (Automations)
The automation groups, typically grouped by purpose — most commonly cross-pipe routing (moving a card
to the matching phase in a parallel pipe) and navigation (moving cards back to a phase) and bulk
operations. Note: trigger/condition details are often not fully exported in the source, so treat the
listed destination/action as the reliable part and expect to confirm conditions manually.

## 5. Agentes de IA (AI Agents)
The AI validators and what they do. In the reference processes these appear as **connectors**, not
native Pipefy agents — an external architecture (e.g., via GCP). Common ones:
- **IQV — Intelligent Quote Validator**: validates supplier quotes; outputs a status label, a
  validator connector, and an error-notification field. Operates in phases like Compliance check,
  Response review, Last action, Closed.
- **ICV — Intelligent Compliance Validator**: validates the request against compliance rules; outputs
  a summary table, an attachment, a passed/not-passed label, and a feedback field.
For each agent the document lists its acting phases, input fields, output fields, and what it does.

Note: in the reference documents these validators are external connectors. When building a new
process, the team prefers to realize these validation intents with **native Pipefy AI agents** rather
than reproducing the external connector architecture — see `decision_catalog.md`.

## 6. Conectores e Pipes Relacionados (Connectors & Related Pipes)
A table of connectors/auxiliary pipes/tables (e.g., Buying instructions, Catalog Insight, change
trackers, the IQV/ICV pipes, the parallel pipe), with their type, the phases where each is used, and
its purpose.

## 7. Decisões de Design (Design Decisions)
A two-column table (dimension → choice made in this case) summarizing the concrete design choices:
data entry, number of pipes, phases, SLA tracking, AHT measurement, AI agents, depth per pipe,
internal connectors, approval (present or not), a technical/system phase, notifications, required
fields, L1/L2 classification, and follow-up scheduling.

## 8. Dimensões de Decisão para o Builder (Builder Decision Dimensions)
The most important section for this skill. A numbered list of the **variation points** for the
process, each phrased as a branching decision ("if yes → do X; if no → do Y"). This is the per-process
source for the offers in step 4 of the build. Consolidating this section across all documents is what
produces `decision_catalog.md`.

## 9. Nível de Maturidade (Maturity Level)
The maturity classification (e.g., Level 3 — Advanced) with the justification and the lists of
elements present vs absent. Use maturity to set expectations about how heavy a build will be.
