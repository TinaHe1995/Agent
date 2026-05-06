---
name: personal-context-sync
description: Load Xingyao's personal memory before work, and synchronize the personal-context skill/repo by downloading, updating, or uploading skill and memory changes. Use when the user asks to clone/update memory, install/update/upload a skill, sync personal context, backfill local agent conversations, or push summarized observations into xingyaoww/.personal-context.
---

# Personal Context Sync

## Mandatory First Step

When this skill is loaded, the first task is to refresh and inspect Xingyao's
personal memory. Do this before answering the user, editing files, or running
the requested workflow.

1. Ensure the personal-context repo exists locally.
2. Verify it points to the allowed remote.
3. Pull the latest `main`.
4. Read the routing and memory files needed for the current task.

Use these defaults:

```bash
CONTEXT_REPO="$HOME/.personal-context"
ALLOWED_REMOTE='xingyaoww/.personal-context'
```

If the repo is missing, download it:

```bash
git clone https://github.com/xingyaoww/.personal-context.git "$HOME/.personal-context"
```

Verify the remote before trusting or writing anything:

```bash
git -C "$HOME/.personal-context" remote get-url --push origin
```

Continue only if the URL points to `xingyaoww/.personal-context`.

Refresh memory:

```bash
git -C "$HOME/.personal-context" fetch origin main
git -C "$HOME/.personal-context" switch main
git -C "$HOME/.personal-context" pull --ff-only origin main
```

Then inspect:

- `AGENTS.md`
- `rules/USER.md`
- `rules/WORKSPACE.md`
- recent `contexts/memory/OBSERVATIONS.md` entries
- task-relevant files found by searching `rules/`, `contexts/`, and `skills/`

Do not continue until this memory check is complete. If refresh fails because
of local changes, network, auth, or conflicts, report the blocker and use the
currently available local memory only if it is safe to do so.

## What This Skill Manages

This skill handles three related workflows.

**Download**

- Clone `xingyaoww/.personal-context` to `$HOME/.personal-context`.
- Install or copy a requested skill from personal context into a target repo or
  local skill directory.
- Preserve the source skill layout: `skill-name/SKILL.md`, plus any referenced
  `agents/`, `scripts/`, `references/`, or `assets/` files.

**Update**

- Pull the latest personal-context `main`.
- Compare the canonical skill source with the installed copy before editing.
- Edit the canonical source when the change should persist across machines.
- Edit a repo-local `.agents/skills/<skill-name>/` copy only when the user wants
  that repo to carry the skill.

**Upload**

- Commit intentional memory or skill changes to a feature branch.
- Push only to the allowed remote for personal-context updates, or to the target
  repository when the user asks for a repo-local skill PR.
- Open a PR; do not merge unless the user explicitly asks.

## Memory Updates From Agent History

Inventory before reading content. For normal workspace sync, check:

```bash
SOURCE_ROOTS=("$HOME/cloud" "$HOME/codecs")
```

When the user asks to backfill local agent conversations, also inspect:

```bash
AGENT_ROOTS=(
  "$HOME/.claude"
  "$HOME/.codex"
  "$HOME/.opencode"
  "$HOME/.openhands"
)
```

Find likely artifacts with `rg --files`; inspect SQLite schemas and counts before
reading rows:

```bash
rg --files "${SOURCE_ROOTS[@]}" "${AGENT_ROOTS[@]}" 2>/dev/null \
  | rg -i '(conversation|transcript|session|history|chat|message|agent|\.jsonl$|\.json$|\.sqlite$|\.db$|\.md$|\.txt$)'
sqlite3 path/to/file.sqlite '.tables'
```

Do not do an unrestricted home-directory scan.

## Extraction Rules For Memory Backfill

Extract future-useful context:

- Explicit user instructions about memory, sync, repo policy, or collaboration
- Repeated technical, product, writing, and workflow preferences
- Durable project context, active long-running projects, and source-of-truth paths
- Workflow friction that should become a rule, skill, or route
- Machine-specific source roots needed for future sync runs

Skip or redact:

- Secrets, tokens, cookies, credentials, private keys, and auth headers
- Raw conversation dumps, full logs, SQLite DBs, screenshots, and transcripts
- Third-party private details unless abstracted and necessary
- One-off task state unless the user explicitly asks to preserve it

Use this confidence scale:

- `High`: direct user instruction, or repeated evidence across time/projects
- `Medium`: clear evidence from one source, useful but not yet global policy
- `Low`: candidate observation; keep it in the report unless promoted

## Write Paths For Memory Backfill

Write one report per sync:

```text
contexts/survey_sessions/activity_mining/agent_conversation_sync_YYYYMMDD.md
```

Use this structure:

```markdown
# Agent Conversation Sync - YYYY-MM-DD

## Scope
- Machine:
- Source roots:
- Optional agent roots:
- Time range:
- Files inspected:
- Files skipped:

## Source Inventory
| Source | Type | Time range | Count / size | Notes |
|--------|------|------------|--------------|-------|

## New Observations
| Confidence | Observation | Evidence | Destination |
|------------|-------------|----------|-------------|

## Applied Updates
- `contexts/memory/OBSERVATIONS.md`: ...
- `rules/USER.md`: ...
- `rules/WORKSPACE.md`: ...

## Gaps / Follow-ups
- ...
```

Then update:

1. `contexts/memory/OBSERVATIONS.md` for dated, evidence-backed observations.
2. `rules/USER.md` only for high-confidence durable facts and preferences.
3. `rules/WORKSPACE.md` for durable local/repo/source routing.
4. `AGENTS.md` only for global behavior rules.
5. `rules/axioms/` only when the user explicitly asks for axiom/cognitive
   extraction.

## Skill Update Rules

When updating a skill:

- Keep `SKILL.md` concise enough to load cheaply.
- Put deterministic or repeated commands in `scripts/` only when they are worth
  maintaining.
- Keep detailed domain docs in `references/` and link them from `SKILL.md`.
- Do not add README/changelog files inside a skill unless the repository already
  requires them.
- If the skill is copied into a repo, keep the copy self-contained. Avoid
  symlinks unless the target repo already relies on symlinked skills.

## QA Before Commit

Stage only intentional files, then run:

```bash
git diff --cached --check
rg -n '^<<<<<<<|^=======$|^>>>>>>>' \
  AGENTS.md rules contexts skills marketplaces plugins .agents .plugin \
  .codex-plugin .claude-plugin 2>/dev/null
```

Check that raw conversation artifacts are not staged:

```bash
git diff --cached --name-only \
  | rg -i '(conversation|transcript|session|history|chat|message|jsonl|sqlite|\.db$|\.log$)' \
  | rg -v '^contexts/survey_sessions/activity_mining/agent_conversation_sync_'
```

Scan the staged diff for credentials:

```bash
git diff --cached \
  | rg -n -i '(api[_-]?key|secret|token|password|cookie|authorization:|bearer |BEGIN (RSA|OPENSSH|PRIVATE) KEY)'
```

Instructional matches are acceptable after review. Real credentials or raw
private data must be redacted before committing.

## Commit And PR For Personal Context

Start from `origin/main` before creating the sync branch:

```bash
git fetch origin main
git switch -c context-sync/YYYYMMDD origin/main
```

Commit with a concise message, push the current branch, and open a PR:

```bash
git commit -m "Sync personal context from local agent history"
git push -u origin HEAD
gh pr create --base main --head "$(git branch --show-current)" \
  --title "Sync personal context from local agent history" \
  --body "Updates personal context from local agent history."
```

Report the source scope, updated files, commit hash, PR URL, and skipped roots.

For a repo-local skill PR, follow that repository's contribution rules. Stage
only the skill files, run the most relevant file-level checks, commit with the
repo's required trailers, push a dedicated branch, and open a PR against the
target repo's default branch.
