# Discovery Questions — Consultative Intake (minimal, with suggestions)

You consult the knowledge base **before** this step, so you already know the standard shape of the
process. Ask only the few things that the historical knowledge cannot answer — just enough to direct
and customize the solution. Keep it short.

**Always present selectable suggestions** for every question (a few options to tap, including your
recommended default) so the user types as little as possible. Reserve open text for when no sensible
options exist. Pace the questions — a few at a time — and ask in the user's language (Portuguese by
default). As answers arrive, recommend the best practice; this is consulting, not a form.

Each theme gives the question, suggested options, and what the answer informs.

## 0. Perfil do cliente (sempre, antes do grounding)
- "País/idioma da operação, porte aproximado (até 500 / 500–5.000 / 5.000+ pessoas), e o cliente
  **permite agentes de IA** por contrato?"
- → Decide o locale/fuso dos e-mails (`pt-BR`/`America/Sao_Paulo` para operação brasileira) e se a
  porta de agente de IA fica disponível na consultoria de variações.

## 1. Process & fit (usually known from step 1 — only confirm if needed)
- "Confirma o processo e o objetivo? O que dispara o início e o que encerra?"
- Options: confirm, or pick the domain. → Confirms scope and the Pipefy-fit check.

## 2. Origin & systems
- "Como as requisições entram no processo?"
- Options: `Manual (formulário)` · `Via sistema externo (ERP/SAP)` · `Via iPaaS` · `Outro`
- → Start form vs API entry; HTTP via the Service Account.

Quando a resposta envolver sistema externo ou iPaaS, complete antes de aprovar o spec:
- "Qual pipe será o dono do flow e qual evento o dispara?"
- "Quais dados entram, quais passos/pieces transformam esses dados e qual resultado volta ao processo?"
- "Já existe uma conexão autorizada para esse app?" Se houver mais de uma, peça o `externalId` ou
  nome inequívoco; se não houver, registre a criação da conexão como pendência manual.
- "O teste pode causar efeito externo?" Se sim, defina dados descartáveis e registre que o teste
  exigirá aprovação explícita separada, assim como a publicação do flow.

## 3. Volume
- "Qual o volume esperado?"
- Options: `Até ~50/dia` · `~50–200/dia` · `200+/dia` · `Ainda não sei`
- → Whether a system/bulk phase is justified; import strategy; Pipe vs Database.

## 4. Languages & regions
- "Idioma(s) e regiões?"
- Options: `1 idioma` · `Vários idiomas, mesmo processo` · `Muda de fato por região`
- → One multi-language pipe (default) vs a management pipe + Interface (exception).

## 5. SLAs
- "Há SLA por etapa?"
- Options: `Sim, por etapa` · `Não — definir expectativa alta` · `Só ponta a ponta`
- → SLA per phase vs a single rule-based due date; set a high expectation if none.

## 6. Approvals & controls
- "Há aprovações no processo?"
- Options: `Sim, por valor/limite` · `Sim, outro critério` · `Sem aprovação`
- → The approval pattern; critical movements via automation/buttons, not manual.

## 7. Documents & AI
- "Lida com documentos, ou precisa de dado externo em tempo real?"
- Options: `Documentos (cotações/notas/contratos)` · `Dado em tempo real (ex.: câmbio)` · `Ambos` · `Nenhum`
- → Native AI agents: AI + IDP for documents, AI + Websearch for real-time data.

## 8. External stakeholders
- "Pessoas de fora do processo participam?"
- Options: `Só internos` · `Externos enviam dados` · `Externos só acompanham`
- → Interface or Portal vs Phase Form (mind paid licenses).

## 9. Adjustments / rework
- "Tem um vai-e-vem de ajuste antes de seguir?"
- Options: `Sim` · `Não`
- → The dedicated "Ajuste" phase pattern.

## 10. Actors & permissions
- "Times diferentes precisam de acessos diferentes?"
- Options: `Sim` · `Não`
- → Single vs multiple pipes; access via groups.
