#!/usr/bin/env python3
"""Re-apply our customizations onto a fresh upstream ai-toolkit checkout.

Currently one perk: ``create_email_template`` (the /graphql/core endpoint), which
upstream does not ship. Upstream only has get/send of templates.

WHY A PYTHON PATCHER AND NOT ``git apply``
    A textual .patch breaks the moment upstream touches a nearby line, and can
    apply *partially* — leaving a half-wired tree that imports fine but fails at
    runtime. This patcher instead:
      * matches on semantic ANCHORS (a distinctive code fragment), not line numbers
      * is IDEMPOTENT (already-patched trees are left alone, exit 0)
      * VERIFIES every edit landed, and exits non-zero with a clear reason if not

    An upstream refactor should make this script FAIL LOUDLY, so the installer
    falls back to the bundled known-good payload, rather than shipping a broken
    tree. Failure here is the designed safety net, not a bug.

Usage:
    python apply-pipefy-perks.py <path-to-ai-toolkit-root>

Exit codes:
    0 = perks present (applied now, or already there)
    2 = an anchor was missing / verification failed -> caller should fall back
"""

from __future__ import annotations

import sys
from pathlib import Path

# --- perk payloads -------------------------------------------------------

CORE_URL_PROP = '''
    @computed_field  # type: ignore[prop-decorator]
    @property
    def core_graphql_url(self) -> str:
        """Core GraphQL endpoint (e.g. email templates), derived from ``base_url``."""
        return f"{self.base_url.rstrip('/')}/graphql/core"
'''

CREATE_MUTATION = '''
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

'''

SERVICE_METHOD = '''
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
'''

CLIENT_METHOD = '''
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
            repo_id,
            name,
            subject,
            body,
            from_name,
            from_email,
            to_email,
            cc_email=cc_email,
            bcc_email=bcc_email,
            locale=locale,
            time_zone=time_zone,
        )
'''

MCP_TOOL = '''
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
            """Create an email template on a pipe or table.

            Uses the /graphql/core endpoint (derived from the configured host, so
            it works on single-tenant deployments). The template can then be used
            by send_email_with_template.

            Args:
                repo_id: Pipe or table ID that will own the template.
                name: Template name.
                subject: Email subject line.
                body: Email body as HTML. Placeholders like {{card.title}} are allowed.
                from_name: Display name of the sender.
                from_email: Sender address; may use placeholders.
                to_email: Recipient address; may use placeholders.
                cc_email: Optional CC address(es).
                bcc_email: Optional BCC address(es).
                locale: Template locale (default en-US).
                time_zone: Template time zone (default Etc/Universal).
                debug: When True, append GraphQL codes and correlation_id to errors.
            """
            client = get_pipefy_client(ctx)
            rid, err = validate_tool_id(repo_id, "repo_id")
            if err is not None:
                return err
            for value, label in (
                (name, "name"),
                (subject, "subject"),
                (body, "body"),
                (from_name, "from_name"),
                (from_email, "from_email"),
                (to_email, "to_email"),
            ):
                if not isinstance(value, str) or not value.strip():
                    return build_webhook_error_payload(
                        message=f"Invalid '{label}': provide a non-empty string.",
                    )
            try:
                raw = await client.create_email_template(
                    rid,
                    name,
                    subject,
                    body,
                    from_name,
                    from_email,
                    to_email,
                    cc_email=cc_email,
                    bcc_email=bcc_email,
                    locale=locale,
                    time_zone=time_zone,
                )
            except ValueError as exc:
                return build_webhook_error_payload(message=str(exc))
            except Exception as exc:  # noqa: BLE001
                return handle_webhook_tool_graphql_error(
                    exc,
                    "Create email template failed.",
                    debug=debug,
                    resource_kind="pipe",
                    resource_id=str(repo_id),
                )
            return build_webhook_success_payload(
                message="Email template created.",
                data=raw,
            )
'''

# --- edit plan -----------------------------------------------------------
# Each edit: (relative path, skip_if, anchor, replacement_for_anchor)
# "skip_if" present in the file => that edit is already applied.

SDK = "packages/sdk/src/pipefy_sdk"
MCP = "packages/mcp/src/pipefy_mcp"

EDITS: list[tuple[str, str, str, str]] = [
    # 1. settings: the /graphql/core computed URL
    (
        f"{SDK}/settings.py",
        "def core_graphql_url",
        '        return f"{self.base_url.rstrip(\'/\')}/graphql/interfaces"\n',
        '        return f"{self.base_url.rstrip(\'/\')}/graphql/interfaces"\n'
        + CORE_URL_PROP,
    ),
    # 2a. queries: the mutation constant
    (
        f"{SDK}/queries/webhook_queries.py",
        "CREATE_EMAIL_TEMPLATE_MUTATION = gql",
        "__all__ = [\n",
        CREATE_MUTATION + "__all__ = [\n",
    ),
    # 2b. queries: export it
    (
        f"{SDK}/queries/webhook_queries.py",
        '"CREATE_EMAIL_TEMPLATE_MUTATION"',
        '    "CREATE_AND_SEND_INBOX_EMAIL_MUTATION",\n',
        '    "CREATE_AND_SEND_INBOX_EMAIL_MUTATION",\n'
        '    "CREATE_EMAIL_TEMPLATE_MUTATION",\n',
    ),
    # 3a. service: import the mutation
    (
        f"{SDK}/services/webhook_service.py",
        "    CREATE_EMAIL_TEMPLATE_MUTATION,",
        "from pipefy_sdk.queries.webhook_queries import (\n"
        "    CREATE_AND_SEND_INBOX_EMAIL_MUTATION,\n",
        "from pipefy_sdk.queries.webhook_queries import (\n"
        "    CREATE_AND_SEND_INBOX_EMAIL_MUTATION,\n"
        "    CREATE_EMAIL_TEMPLATE_MUTATION,\n",
    ),
    # 3b. service: accept the core executor
    (
        f"{SDK}/services/webhook_service.py",
        "core_executor",
        "        executor: GraphQLExecutor,\n",
        "        executor: GraphQLExecutor,\n"
        "        core_executor: GraphQLExecutor,\n",
    ),
    # 3c. service: store it
    (
        f"{SDK}/services/webhook_service.py",
        "self._core_executor",
        "        self._executor = executor\n",
        "        self._executor = executor\n"
        "        # Email templates are created against /graphql/core (sibling of\n"
        "        # /graphql); host still derives from base_url, so ST works.\n"
        "        self._core_executor = core_executor\n",
    ),
    # 3d. service: the method itself
    (
        f"{SDK}/services/webhook_service.py",
        "async def create_email_template",
        "    async def _resolve_repo_id(",
        SERVICE_METHOD + "\n    async def _resolve_repo_id(",
    ),
    # 4a. client: Executors gains .core
    (
        f"{SDK}/client.py",
        "core: GraphQLExecutor",
        "    public: GraphQLExecutor\n    interfaces: GraphQLExecutor\n    internal: GraphQLExecutor\n",
        "    public: GraphQLExecutor\n    interfaces: GraphQLExecutor\n    internal: GraphQLExecutor\n    core: GraphQLExecutor\n",
    ),
    # 4b. client: PipefyEndpoints gains .core
    (
        f"{SDK}/client.py",
        "core: GraphQLEndpoint",
        "    public: GraphQLEndpoint\n    interfaces: GraphQLEndpoint\n    internal: GraphQLEndpoint\n",
        "    public: GraphQLEndpoint\n    interfaces: GraphQLEndpoint\n    internal: GraphQLEndpoint\n    core: GraphQLEndpoint\n",
    ),
    # 4c. client: build the core endpoint
    (
        f"{SDK}/client.py",
        "url=settings.core_graphql_url",
        "        internal=GraphQLEndpoint(\n"
        "            url=settings.internal_api_url,\n"
        "            cache_schema=cache_schema,\n"
        "            headers=headers,\n"
        "        ),\n",
        "        internal=GraphQLEndpoint(\n"
        "            url=settings.internal_api_url,\n"
        "            cache_schema=cache_schema,\n"
        "            headers=headers,\n"
        "        ),\n"
        "        core=GraphQLEndpoint(\n"
        "            url=settings.core_graphql_url,\n"
        "            cache_schema=cache_schema,\n"
        "            headers=headers,\n"
        "        ),\n",
    ),
    # 4d. client: bind the core executor
    (
        f"{SDK}/client.py",
        "core=AuthenticatedExecutor",
        "        internal=AuthenticatedExecutor(endpoint=endpoints.internal, auth=auth),\n",
        "        internal=AuthenticatedExecutor(endpoint=endpoints.internal, auth=auth),\n"
        "        core=AuthenticatedExecutor(endpoint=endpoints.core, auth=auth),\n",
    ),
    # 4e. client: pass it to WebhookService
    (
        f"{SDK}/client.py",
        "core_executor=ex.core",
        "        self._webhook_service = WebhookService(\n            executor=ex.public,\n",
        "        self._webhook_service = WebhookService(\n            executor=ex.public,\n            core_executor=ex.core,\n",
    ),
    # 4f. client: public facade method
    (
        f"{SDK}/client.py",
        "async def create_email_template",
        "    async def send_email_with_template(\n",
        CLIENT_METHOD + "\n    async def send_email_with_template(\n",
    ),
    # 5. mcp: the tool wrapper
    (
        f"{MCP}/tools/webhook_tools.py",
        "async def create_email_template",
        "        @mcp.tool(\n            annotations=ToolAnnotations(readOnlyHint=True),\n            meta=REMOTE,\n        )\n        async def get_webhooks(",
        MCP_TOOL
        + "\n        @mcp.tool(\n            annotations=ToolAnnotations(readOnlyHint=True),\n            meta=REMOTE,\n        )\n        async def get_webhooks(",
    ),
    # 6. mcp: register the tool name
    (
        f"{MCP}/tools/registry.py",
        '"create_email_template"',
        '        "create_phase",\n',
        '        "create_email_template",\n        "create_phase",\n',
    ),
]

# Symbols that MUST exist after patching, or we did not really succeed.
VERIFY: list[tuple[str, str]] = [
    (f"{SDK}/settings.py", "def core_graphql_url"),
    (f"{SDK}/queries/webhook_queries.py", "CREATE_EMAIL_TEMPLATE_MUTATION = gql"),
    (f"{SDK}/services/webhook_service.py", "self._core_executor.execute_query"),
    (f"{SDK}/client.py", "core=AuthenticatedExecutor"),
    (f"{SDK}/client.py", "core_executor=ex.core"),
    (f"{MCP}/tools/webhook_tools.py", "async def create_email_template"),
    (f"{MCP}/tools/registry.py", '"create_email_template"'),
]


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: apply-pipefy-perks.py <ai-toolkit-root>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1])
    if not (root / "packages" / "mcp").is_dir():
        print(f"FAIL: not an ai-toolkit root: {root}", file=sys.stderr)
        return 2

    applied = skipped = 0
    for rel, skip_if, anchor, replacement in EDITS:
        path = root / rel
        if not path.is_file():
            print(f"FAIL: missing file {rel} (upstream layout changed?)", file=sys.stderr)
            return 2
        text = path.read_text(encoding="utf-8")
        if skip_if in text:
            skipped += 1
            continue
        count = text.count(anchor)
        if count != 1:
            print(
                f"FAIL: anchor for {rel} found {count} times, expected exactly 1 "
                f"(upstream refactored this area). Anchor: {anchor.strip()[:70]!r}",
                file=sys.stderr,
            )
            return 2
        path.write_text(text.replace(anchor, replacement, 1), encoding="utf-8")
        applied += 1

    for rel, symbol in VERIFY:
        text = (root / rel).read_text(encoding="utf-8")
        if symbol not in text:
            print(f"FAIL: verification missed {symbol!r} in {rel}", file=sys.stderr)
            return 2

    # Syntax gate: a broken insertion must not reach pip.
    import py_compile

    for rel in sorted({rel for rel, _, _, _ in EDITS}):
        try:
            py_compile.compile(str(root / rel), doraise=True, cfile=None)
        except py_compile.PyCompileError as exc:
            print(f"FAIL: {rel} does not compile after patching: {exc}", file=sys.stderr)
            return 2

    print(f"PERKS_OK (applied={applied}, already_present={skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
