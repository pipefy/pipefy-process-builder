# Modeling Best Practices (Boas Práticas de Modelagem) — Pipefy

The team's mandatory modeling rules, from the "Guia de Boas Práticas de Modelagem." Apply these
throughout a build, alongside the naming standard in `nomenclature.md`. They protect traceability,
integrations, and maintainability.

Contents:
0. Foundation — the One Pager · 1. Strategy & initial architecture · 2. Fields & naming ·
3. Display logic & flow · 4. Assignees · 5. HTTP automations · 6. Import strategy · 7. Pipefy AI ·
8. Security · 9. Interface / Portal / Phase Form · 10. Fit with Pipefy · 11. Permissions ·
12. Email & messaging · 13. Time & time zones.

## 0. Foundation — the One Pager
Following `nomenclature.md` is mandatory before any configuration. Standardized names for pipes,
phases, fields, and automations keep processes auditable instead of becoming "black boxes."

## 1. Strategy & initial architecture (decide before creating fields)
- **One movement logic.** Choose a single approach for movements and field updates — do not mix
  automations and flows; centralize on one.
- **Single vs multiple pipes.** Split into a new pipe when scope changes (e.g., an order becomes a
  quote), for 1-to-N relationships, or when different teams need different permissions.
- **"Magic number" of phases: 10–15.** Above 15 is "exotic"; bellow 10, evaluate splitting.
- **Phase colors = responsibility.** Phases handled by similar agents (all approvers, all requesters)
  share the same color for visual readability.
- **No empty "management pipes."** Don't create status-only pipes; use Interfaces for the macro view.
  Exception: processes that genuinely differ by region/language (different conditionals per region) —
  you may build a management pipe consolidating what's common and build the Interface from it.
- **Multiple languages → one process.** Prefer a single process carrying all languages, with one
  centralized language field (show other languages in descriptions). Exception: if the client demands
  an individualized experience, use fields per language but keep one general field that centralizes
  the values for automations/integrations.
- **Pipe vs Database.** Prefer Pipes (they allow bulk actions). Use Databases only for static, fixed
  information with a limited number of records.
- **Final documentation.** Map the full process and store it in the pipe description (the
  documentation-creation pipe plus an AI can help assemble the movement flow).
- **SLAs — always discuss with the client.** If a phase has no SLA, set a high expectation (the
  longest fair time for the step) and refine over use.
  - *SLA de fase:* tracks a phase's due date.
  - *SLA de vencimento:* a single due-date field driven by a rule; keep one due-date field plus
    several datetime fields to register the various due dates, minding which date feeds which rule.
- **Safe movement.** Critical movements (approvals/adjustments) go through automation or buttons,
  never manual drag.

## 2. Fields & naming
- **Clean IDs.** When creating fields (especially in homologação), use a simple name with no special
  characters first to generate the ID, then rename to the final label.
- **Never duplicate fields.** Cloning changes IDs unpredictably and breaks integrations and automation
  logic.
- **Don't number fields** (e.g., "1. Nome") — order may change and that causes rework.

## 3. Display logic & flow
- **One "hide-all" conditional per phase** to hide every field and show only what's needed; this
  avoids latency conflicts and eases maintenance by others.
- **Adjustment ("vai e vem") flow:**
  - Create a dedicated "Ajuste/Arrumar" phase.
  - Clear fields via HTTP calls (mutation with `null`), consistently.
  - Keep a long-text field logging the adjustment history with date/time before clearing inputs.
  - Use labels to mark a card as an adjustment return.
  - Set a max SLA for the adjustment to be sent back.
  - If the client has iPaaS, a counter field for number of adjustments is ideal — but if the whole
    movement is via automation, a counter is costly and not recommended.
- In sent phase forms, reveal the trigger field (the one that fires automations/integrations) only
  after all fields — or the last field — are filled.

## 4. Assignees
- **Always assign a responsible** to the card; cards should not sit "loose."
- Enable the pipe option "allow editing only for those responsible for the card."
- **Always desync** assignee and label fields.
- **Assign via HTTP** so you can use "add member" instead of "replace," keeping the person responsible
  across phases.
- Use no more than one assignee field per phase.
- For multiple assignees, register them in a Database field, then add to the assignee field.

## 5. HTTP automations
- **Service Account token only.** HTTP automations must use the Service Account token; never connect
  Pipefy to personal apps. If an SC leaves, personal connections (null-cleanup, add-assignee) can
  break. If you find personal connections in old automations/recipes, replace them proactively — don't
  wait for breakage.
- A **dedicated Service Account per department** (or similar) is strongly recommended to segment
  access and ease audits.
- Clear fields via HTTP (mutation `null`) consistently across all needed fields.
- Mind attachment handling via HTTP when updating to null.

## 6. Import strategy
- Don't use the native Importer when the process has connected fields or high data volume.
- For large volumes, create a dedicated import pipe; its first phase should have a long-text field for
  an error log.

## 7. Pipefy AI
Updates are frequent — keep this lightweight and verify current capabilities at build time.
- **Prefer AI 2.0 agents** (1.0 will eventually be deprecated).
- A single automation can carry multiple actions; when multiple behaviors are directed, verify all
  ran.
- **AI + IDP (Intelligent Document Processing):** use when documents must be read — JPEG, PNG, PDF
  accepted; standardized/governmental documents with complex tables are the focus. Tell the client it
  raises consumption.
- **AI + Websearch:** use when the process needs real-time external data (e.g., USD quote). Tell the
  client it raises consumption, and **validate the use with the AI team** — confirm where the query
  runs and beware unreliable sources (fake news). It brings external context, breaks information
  silos, and increases precision in tasks that depend on constantly changing variables.

## 8. Security
- Keep Pipes **private**.
- Restrict editing to the card's responsible; allow card **deletion only by admins**.
- Make the Start Form available **only to pipe members/users**.

## 9. Interface / Portal / Phase Form
- **Interface** — for people outside the process (stakeholder, requester, external supplier). Mind
  paid licenses. Use it to give input / a field or two / visibility, not to "work" the process. It can
  centralize several pipes on one page and, in approval processes, multiple approvals on one screen.
- **Portal** — centralizes all of one company's forms on a single page.
- **Phase Form** — when conditional business rules must be met/shown, or when an approver/requester
  needs to edit fields (enable editing instead of creating many fields).
- Portal and Interface both support cascading filters.

## 10. Fit with Pipefy
Some requests don't fit the product. A process likely does **not** fit Pipefy when it is:
- a single-phase process;
- only an email dispatch (marketing);
- inventory / scheduling / time-clock control;
- real-time tied to an external source (race condition);
- an attempt to replace an ERP with Pipefy.
If the request matches one of these, say so plainly rather than forcing a build.

## 11. Permissions
- Manage access via groups. People in the same area should not always share access to the same pipes.
- Works well with Active Directory (users assigned to groups by role/team).
- Without AD: Pipefy's webhook for new users can automate group inclusion together with a governance
  pipe; an existing user changing roles needs configuration or a manual process aligned with the
  client.

## 12. Email & messaging
- Build and validate a **standard email template before** configuring, to avoid repeated
  change/validation cycles.
- Use **HTML** for structured, professional, brand-aligned emails.
- For images, upload to a reliable public server and insert via an HTML tag (or the native editor),
  ensuring a permanent link.
- **Attachments:** one attachment field per email. For the "generate hyperlink" function, attach only
  one file — two or more in the same hyperlink breaks sending.
- Pipefy has **no native auto-reply** to received emails with a predefined template; design around
  this limitation.
- For dynamic corporate signatures, avoid fixed images; build the signature with HTML where card
  variables feed the dynamic data, pulling a single user-name field consistently.

## 13. Time & time zones
- Pipefy inherits regional preferences; each user must set their time zone in their profile to avoid
  divergences in history and movement times.
- In any deadline/SLA automation, **explicitly select the correct time zone** in the rule so triggers
  fire at the exact moment regardless of where the server is hosted.
