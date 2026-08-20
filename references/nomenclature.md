# Official Naming Standard (Nomenclatura) — Pipefy & Integrations

This is the team's official naming standard, from the "One Pager — Nomenclatura Oficial." **Every**
element you create in Pipefy must follow it. The bracket tags (e.g., `[Inativo]`, `[Auxiliar]`,
`[Integração]`, `[ABR]`, `z[DEV]`, `Z[legacy]`) are literal and must be reproduced exactly. The
descriptive parts (scenario, action, purpose, field label, pipe name) are filled in the user's
language (Portuguese by default).

Consistent naming is what keeps the ecosystem auditable and lets iPaaS integrations run without
errors — unstandardized names turn processes into un-auditable "black boxes."

## Pipefy

### Automations
`[Fase gatilho] Cenário (condição) -> Ação`
- Include `(condição)` only when more than one automation shares the same scenario.

### Conditionals
`[Esconder/Exibir] Campo relacionado = opção`

### Email templates
`[Fase específica] Finalidade -> Destinatário (Interno/Externo)`

### Fields
- **Inactive:** `[Inativo] Campo` — also add the field description "Não deletar".
- **Hidden (workaround):** `[Integração] Campo` and `[Auxiliar] Campo` — also add the description
  "Não deletar".

### Pipe names
- **Area abbreviation:** `[ABR] Nome Pipe`
- **In development:** `z[DEV] Nome Pipe`
- **Inactive pipes:** `Z[legacy] Nome Pipe`
- **Auxiliary pipes:** `[Auxiliar] Nome Pipe`
- **Related pipes:** `[Auxiliar] 1/3 Nome Pipe` (the `1/3` indicates position within a related set)

### Other
- **Connections (on the pipe):** `Nome do Pipe`
- **Phase description:** `SLA + Responsável` and a brief orientation.
- **Pipe description:** the process objective, what happens in each step, and the stakeholder
  responsible for the process.

## Integration (iPaaS)

### Folder hierarchy (levels)
- Organização
  - Departamento/Área (Projeto)
    - Processo (Pasta)
      - Software (ativo)
      - Software (inativo)
    - Conexões

### Recipes
`[Fase gatilho] Cenário -> Ação`

### Connections
- `[Service account] Nome da conexão`
- `[Username/Email da conexão] Nome da conexão`

### Actions
Use a clear description on every step.
