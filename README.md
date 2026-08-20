# Pipefy Process Builder

Reusable skill for diagnosing, creating, and evolving Pipefy processes. `SKILL.md` is the entry
point; `references/` contains the stage playbooks and handoff contracts.

## Development

Work on `feat/ipaas-workflow-support` until the pull request is merged. Runtime engagement artifacts
belong in `builds/` and are intentionally ignored by Git.

## Local sync shared skill copies

This workstation keeps `scripts\sync-global-skill.ps1` locally. It is deliberately ignored by Git:
it deploys the current checkout to installed agent directories and must not be published with the
reusable skill. After pulling an approved repository update, run it from the repository root:

```powershell
.\scripts\sync-global-skill.ps1
```

The local script replaces and SHA-256 verifies these shared copies:

- `%USERPROFILE%\.agents\skills\pipefy-process-builder`
- `%USERPROFILE%\.codex\skills\pipefy-process-builder`
- `%USERPROFILE%\.claude\skills\pipefy-process-builder`
- `%USERPROFILE%\.cursor\skills-cursor\pipefy-process-builder`

To update only one location, pass `-Target agents`, `-Target codex`, `-Target claude`, or `-Target
cursor`. `-Target both` remains available for the `.agents` and Codex pair. Use `-WhatIf` to preview
the replacement without writing. The script deploys only `SKILL.md` and `references/`; it never
copies the Git repository, runtime builds, or credentials.
