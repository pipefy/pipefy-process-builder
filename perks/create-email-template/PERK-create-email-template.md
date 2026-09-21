# Perk: `create_email_template` via `/graphql/core`

Customização própria: o upstream `pipefy/ai-toolkit` **não** tem criação de template
de email. Ele só tem leitura e envio:

| Tool upstream | O que faz |
|---|---|
| `get_email_templates` | lista templates de um pipe/table |
| `send_email_with_template` | envia email usando um template existente |
| `send_inbox_email` | envia email avulso pela inbox do card |
| `get_card_inbox_emails` | lista emails do card |

O que falta é **criar** o template. A mutation `createEmailTemplate` não vive no
endpoint GraphQL padrão (`/graphql`): ela fica em `/graphql/core`, um endpoint
irmão. Por isso o perk não é só "mais uma tool" — precisa de um executor GraphQL
adicional atravessando a injeção de dependência do SDK.

## Por que não é um `.patch`

O upstream refatora essa área com frequência. Entre a v0.2.0-beta.4 e a
v0.4.0-beta.2 ele trocou `BasePipefyClient` (que aceitava `url_override` por
chamada) por um modelo de **executors injetados** (`.public`, `.interfaces`,
`.internal`). Um patch textual falharia — ou, pior, aplicaria pela metade e
deixaria uma árvore que importa mas quebra em runtime.

A forma confiável é o `apply-pipefy-perks.py`: ele casa por **anchors
semânticos**, é idempotente, verifica cada edição e roda `py_compile` no final.
Se o upstream mexer na área, ele **falha alto** (exit 2) em vez de entregar algo
meio aplicado — e o instalador cai no payload embutido.

---

## As 6 edições

Caminhos relativos à raiz do `ai-toolkit`.
`SDK = packages/sdk/src/pipefy_sdk` · `MCP = packages/mcp/src/pipefy_mcp`

### 1. `SDK/settings.py` — a URL derivada

Logo depois da propriedade `interfaces_graphql_url`:

```python
    @computed_field  # type: ignore[prop-decorator]
    @property
    def core_graphql_url(self) -> str:
        """Core GraphQL endpoint (e.g. email templates), derived from ``base_url``."""
        return f"{self.base_url.rstrip('/')}/graphql/core"
```

Deriva de `base_url`, então single-tenant funciona sem nada a mais:
`https://cmpc.pipefy.com` → `https://cmpc.pipefy.com/graphql/core`.

### 2. `SDK/queries/webhook_queries.py` — a mutation

Antes do `__all__`:

```python
CREATE_EMAIL_TEMPLATE_MUTATION = gql(
    """
    mutation createEmailTemplate($bccEmail: String, $body: String!, $ccEmail: String, $fromEmail: String!, $fromName: String!, $name: String!, $repoId: ID!, $subject: String!, $toEmail: String!, $timeZone: String!, $locale: String!) {
      createEmailTemplate(
        input: {bccEmail: $bccEmail, body: $body, ccEmail: $ccEmail, fromEmail: $fromEmail, fromName: $fromName, name: $name, repoId: $repoId, subject: $subject, toEmail: $toEmail, timeZone: $timeZone, locale: $locale}
      ) {
        id
        name
        __typename
      }
    }
    """
)
```

E adicionar `"CREATE_EMAIL_TEMPLATE_MUTATION",` na lista `__all__`.

### 3. `SDK/services/webhook_service.py` — o service

Três mudanças. No bloco de import das queries, acrescentar
`CREATE_EMAIL_TEMPLATE_MUTATION,`. No `__init__`, receber e guardar o executor
do core:

```python
    def __init__(
        self,
        *,
        executor: GraphQLExecutor,
        core_executor: GraphQLExecutor,   # <-- novo
        settings: PipefySettings,
        card_service: CardService,
    ) -> None:
        self._executor = executor
        self._core_executor = core_executor   # <-- novo
        self._settings = settings
        self._card_service = card_service
```

E o método, antes de `_resolve_repo_id`:

```python
    async def create_email_template(
        self,
        repo_id: str,
        name: str,
        subject: str,
        body: str,
        from_name: str,
        from_email: str,
        to_email: str,
        *,
        cc_email: str = "",
        bcc_email: str = "",
        locale: str = "en-US",
        time_zone: str = "Etc/Universal",
    ) -> dict[str, Any]:
        """Create an email template on a pipe or table (uses the /graphql/core endpoint)."""
        variables: dict[str, Any] = {
            "repoId": str(repo_id),
            "name": name,
            "subject": subject,
            "body": body,
            "fromName": from_name,
            "fromEmail": from_email,
            "toEmail": to_email,
            "ccEmail": cc_email,
            "bccEmail": bcc_email,
            "locale": locale,
            "timeZone": time_zone,
        }
        return await self._core_executor.execute_query(
            CREATE_EMAIL_TEMPLATE_MUTATION, variables
        )
```

Note o `self._core_executor` — é o ponto inteiro do perk.

### 4. `SDK/client.py` — a fiação (5 pontos)

O executor `core` precisa existir e chegar até o service:

```python
# (a) dataclass Executors
    public: GraphQLExecutor
    interfaces: GraphQLExecutor
    internal: GraphQLExecutor
    core: GraphQLExecutor          # <-- novo

# (b) dataclass PipefyEndpoints
    public: GraphQLEndpoint
    interfaces: GraphQLEndpoint
    internal: GraphQLEndpoint
    core: GraphQLEndpoint          # <-- novo

# (c) em build_endpoints(), ao lado de internal=
        core=GraphQLEndpoint(
            url=settings.core_graphql_url,
            cache_schema=cache_schema,
            headers=headers,
        ),

# (d) em _bind(), ao lado de internal=
        core=AuthenticatedExecutor(endpoint=endpoints.core, auth=auth),

# (e) na construção do WebhookService
        self._webhook_service = WebhookService(
            executor=ex.public,
            core_executor=ex.core,     # <-- novo
            settings=settings,
            card_service=self._card_service,
        )
```

Mais o método público da fachada, antes de `send_email_with_template`:

```python
    async def create_email_template(
        self,
        repo_id: str,
        name: str,
        subject: str,
        body: str,
        from_name: str,
        from_email: str,
        to_email: str,
        *,
        cc_email: str = "",
        bcc_email: str = "",
        locale: str = "en-US",
        time_zone: str = "Etc/Universal",
    ) -> dict[str, Any]:
        """Create an email template on a pipe or table (via the /graphql/core endpoint)."""
        return await self._webhook_service.create_email_template(
            repo_id, name, subject, body, from_name, from_email, to_email,
            cc_email=cc_email, bcc_email=bcc_email,
            locale=locale, time_zone=time_zone,
        )
```

### 5. `MCP/tools/webhook_tools.py` — a tool

Depois de `send_email_with_template`, seguindo a convenção atual do upstream
(`ctx: Context` + `get_pipefy_client(ctx)` + `meta=REMOTE`):

```python
        @mcp.tool(
            annotations=ToolAnnotations(readOnlyHint=False),
            meta=REMOTE,
        )
        async def create_email_template(
            repo_id: PipefyId,
            name: str,
            subject: str,
            body: str,
            from_name: str,
            from_email: str,
            to_email: str,
            ctx: Context,
            cc_email: str = "",
            bcc_email: str = "",
            locale: str = "en-US",
            time_zone: str = "Etc/Universal",
            debug: bool = False,
        ) -> dict[str, Any]:
            """Create an email template on a pipe or table."""
            client = get_pipefy_client(ctx)
            rid, err = validate_tool_id(repo_id, "repo_id")
            if err is not None:
                return err
            for value, label in (
                (name, "name"), (subject, "subject"), (body, "body"),
                (from_name, "from_name"), (from_email, "from_email"),
                (to_email, "to_email"),
            ):
                if not isinstance(value, str) or not value.strip():
                    return build_webhook_error_payload(
                        message=f"Invalid '{label}': provide a non-empty string.",
                    )
            try:
                raw = await client.create_email_template(
                    rid, name, subject, body, from_name, from_email, to_email,
                    cc_email=cc_email, bcc_email=bcc_email,
                    locale=locale, time_zone=time_zone,
                )
            except ValueError as exc:
                return build_webhook_error_payload(message=str(exc))
            except Exception as exc:  # noqa: BLE001
                return handle_webhook_tool_graphql_error(
                    exc, "Create email template failed.", debug=debug,
                    resource_kind="pipe", resource_id=str(repo_id),
                )
            return build_webhook_success_payload(
                message="Email template created.", data=raw,
            )
```

### 6. `MCP/tools/registry.py` — registrar

Adicionar `"create_email_template",` na lista (em ordem alfabética, antes de
`"create_phase"`). **Sem isso a tool não aparece no Claude.**

---

## Como aplicar

### A) Pelo instalador (já é o padrão)

Nada a fazer. A cada execução ele baixa a versão nova do GitHub, roda o patcher,
valida e instala. No log você vê:

```
[perks] PERKS_OK (applied=15, already_present=0)
create_email_template: presente.
```

### B) Patcher em uma árvore de código (para dev / build manual)

```powershell
# 1. Aplicar sobre um checkout do ai-toolkit
python apply-pipefy-perks.py C:\caminho\ai-toolkit

# 2. Instalar os pacotes patchados
& "$env:LOCALAPPDATA\PipefyMCP\venv\Scripts\python.exe" -m pip install `
    C:\caminho\ai-toolkit\packages\infra `
    C:\caminho\ai-toolkit\packages\auth `
    C:\caminho\ai-toolkit\packages\sdk `
    C:\caminho\ai-toolkit\packages\mcp `
    C:\caminho\ai-toolkit\packages\cli
```

O patcher é idempotente: rodar de novo numa árvore já patchada devolve
`already_present=15` e não duplica nada.

### C) Direto no venv instalado (emergência)

Editar os 6 arquivos em
`%LOCALAPPDATA%\PipefyMCP\venv\Lib\site-packages\pipefy_sdk\...` e
`...\pipefy_mcp\...`.

Funciona, mas **é perdido na próxima reinstalação** e não passa pelo
`py_compile` do patcher. Use só para testar rápido; o caminho durável é (A)
ou (B).

---

## Verificar

```powershell
$py = "$env:LOCALAPPDATA\PipefyMCP\venv\Scripts\python.exe"

# a tool está registrada?
& $py -c "from pipefy_mcp.tools import registry as r; print('create_email_template' in open(r.__file__, encoding='utf-8').read())"

# a URL do core deriva certo do host?
& $py -c "from pipefy_sdk.settings import PipefySettings; s=PipefySettings(base_url='https://cmpc.pipefy.com'); print(s.core_graphql_url)"
# -> https://cmpc.pipefy.com/graphql/core
```

No Claude, depois de reiniciar: peça `create_email_template` num pipe de teste.

---

## Limites e riscos

- **Vale só para o MCP local.** O MCP hospedado (`mcp.pipefy.com`) roda código da
  Pipefy e não pode ser patchado. Quem usa o hospedado não tem essa tool.
- **O patcher pode falhar num upstream futuro** e isso é por design: melhor
  falhar e cair no payload conhecido-bom do que instalar meia customização. Se
  o log mostrar `FAIL: anchor ... expected exactly 1`, o anchor citado precisa
  ser reescrito para a nova estrutura.
- **A mutation é interna.** `/graphql/core` e `createEmailTemplate` não estão na
  API pública documentada da Pipefy: podem mudar sem aviso. É o mesmo risco que
  o fork já assumia antes.
- **Testes do upstream:** `core_executor` é obrigatório no `WebhookService`, então
  os testes que o constroem precisam passar o novo kwarg (já tratado no payload
  embutido, incluindo um teste que garante que a chamada vai para o executor
  `core` e não para o público).
