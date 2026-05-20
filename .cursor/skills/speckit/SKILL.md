---
name: speckit
description: GitHub Spec Kit (SDD) workflow for this repo — constitution, specify, clarify, plan, tasks, analyze, implement, and git hooks. Use when the user mentions speckit, spec-kit, /speckit-*, feature specs, plan.md, tasks.md, or working under project-specifications/.specify or specs/.
---

# Spec Kit (this workspace)

Spec Kit skills live in [project-specifications/.agents/skills/](../../project-specifications/.agents/skills/). Cursor loads them from `.cursor/skills/speckit-*` (symlinks to that directory).

## Workspace paths (read first)

| Concept in skill docs | Actual path (from repo root) |
|-----------------------|------------------------------|
| **Spec Kit root** / "repo root" for scripts | `project-specifications/` |
| Active feature directory | `project-specifications/specs/001-event-ledger-api/` (see `.specify/feature.json`) |
| Constitution | `project-specifications/.specify/memory/constitution.md` |
| Bash helpers | `project-specifications/.specify/scripts/bash/` |

When a skill says "run from repo root", `cd` to `project-specifications/` first. Paths like `specs/…` and `.specify/…` are relative to that directory.

Application code for the current feature may live outside `project-specifications/`; read `plan.md` for the real source tree.

## Recommended workflow

```text
constitution (once) → specify → clarify (optional) → plan → tasks → analyze (optional) → implement
```

Optional: `checklist`, `taskstoissues`, and git extension skills (hooks in `.specify/extensions.yml`).

## Invoke a step

1. Identify the step from the user request (or the table below).
2. **Read** the matching skill file and follow it exactly:
   - `.cursor/skills/<skill-name>/SKILL.md`, or
   - `project-specifications/.agents/skills/<skill-name>/SKILL.md`
3. Apply the workspace path table above before running any script.

## Skill index

| Skill | When to use |
|-------|-------------|
| `speckit-constitution` | Define or update project principles in `.specify/memory/constitution.md` |
| `speckit-specify` | New feature: create `spec.md` and feature directory under `specs/` |
| `speckit-clarify` | Resolve up to 5 ambiguities in the spec before planning |
| `speckit-plan` | Produce `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md` |
| `speckit-tasks` | Generate dependency-ordered `tasks.md` |
| `speckit-analyze` | Cross-check spec, plan, and tasks before implementation |
| `speckit-checklist` | Domain checklists (security, UX, etc.) under feature `checklists/` |
| `speckit-implement` | Execute `tasks.md` in the application codebase |
| `speckit-taskstoissues` | Push tasks to GitHub issues |
| `speckit-git-feature` | Create feature branch (hook before specify) |
| `speckit-git-commit` | Auto-commit after a command (hooks) |
| `speckit-git-initialize` | Init git repo |
| `speckit-git-validate` | Validate branch naming |
| `speckit-git-remote` | Detect remote URL |

## Current feature (default context)

- Feature: **001-event-ledger-api**
- Spec: `project-specifications/specs/001-event-ledger-api/spec.md`
- Plan: `project-specifications/specs/001-event-ledger-api/plan.md`
- Tasks: `project-specifications/specs/001-event-ledger-api/tasks.md`

Refresh from `project-specifications/.specify/feature.json` if the active feature changes.

## Extension hooks

If `project-specifications/.specify/extensions.yml` exists, each skill’s pre/post sections describe optional or mandatory hooks (often git commit/feature). Do not evaluate `condition` expressions; follow the skill’s hook output rules.

## Agent context file

After planning, update the `<!-- SPECKIT START -->` … `<!-- SPECKIT END -->` block in repo-root `AGENTS.md` so the current `plan.md` path stays accurate.
