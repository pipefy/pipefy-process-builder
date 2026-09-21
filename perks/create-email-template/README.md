# Perk: `create_email_template` (MCP local)

O servidor MCP upstream (`pipefy/ai-toolkit`) só lê e envia templates de e-mail; **não cria**. A
mutation `createEmailTemplate` vive em `/graphql/core`, um endpoint irmão do `/graphql`, e por isso a
skill não consegue criá-la via `execute_graphql`. Este perk, desenvolvido por um SC do time, adiciona
a tool `create_email_template` ao MCP **local** (não vale para o MCP hospedado `mcp.pipefy.com`).

## Como a skill usa
- No pré-check, a skill verifica se a tool `create_email_template` existe na sessão.
- Com a tool: template de e-mail é item **Nativo** — o Builder cria, relê em `get_email_templates` e
  cria a automação `send_email_template` com o id devolvido (ver `references/connector-rules.md`
  §4.11 e `references/02-builder.md`, passo 7).
- Sem a tool: pendência manual com o conteúdo pronto para colar (comportamento da 3.2), e a entrega
  aponta para esta pasta.

## Instalar
Siga `PERK-create-email-template.md` (seções "Como aplicar" e "Verificar"). Resumo: rode
`python apply-pipefy-perks.py <raiz do ai-toolkit>` sobre um checkout do upstream e instale os
pacotes no venv do MCP local. O patcher é idempotente e falha alto se o upstream mudar a área.

## Parâmetros da tool
`repo_id` (pipe ou tabela dono), `name`, `subject`, `body` (HTML; placeholders como `{{card.title}}`),
`from_name`, `from_email`, `to_email` (aceitam placeholders), `cc_email`, `bcc_email`,
`locale` (default `en-US` — usar `pt-BR` para clientes brasileiros), `time_zone` (default
`Etc/Universal` — usar `America/Sao_Paulo` quando o processo for brasileiro), `debug`.

## Limites e riscos
- Só MCP local. Mutation interna, fora da API pública: pode mudar sem aviso.
- Se `apply-pipefy-perks.py` falhar com `FAIL: anchor ...`, o upstream refatorou a área — não
  instale meia customização; ajuste o anchor ou aguarde.
