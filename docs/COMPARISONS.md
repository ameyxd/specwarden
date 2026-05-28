# Comparisons

This document compares specwarden with tools that occupy adjacent or overlapping space. The goal is honest positioning, not advocacy.

---

## GitHub Spec Kit (`github/spec-kit`)

### What it is

GitHub's official toolkit for Spec-Driven Development with AI coding agents, launched in May 2026. Ships as a `specify` CLI tool installable via `uv tool install` or `pipx`, plus a set of markdown templates and slash commands (`/speckit.constitution`, `/speckit.specify`, `/speckit.clarify`, `/speckit.plan`, `/speckit.tasks`, `/speckit.implement`) that load into 30+ supported AI agent hosts including Claude Code, GitHub Copilot, and others. The workflow walks the developer through six structured phases — establish project principles, describe what to build, resolve ambiguities, plan the tech stack, break into tasks, execute.

### What it shares with specwarden

Both are tools for spec-driven development with AI coding agents. Both ship a CLI plus agent-side artifacts (slash commands, templates). Both treat the spec as a first-class file in the project, not just a prompt-time instruction. Both target the same failure modes: agents that start editing before the requirements are settled, silent assumptions that get baked into code, scope creep mid-implementation.

### What is different

The enforcement mechanism. The spec-kit README states plainly: *"There is no file-blocking mechanism — enforcement is behavioral (agents follow instructions in templates) rather than gatekeeping."* The `/speckit.implement` step validates that prerequisites exist (constitution, spec, plan, tasks) but does not block file edits that bypass the workflow.

specwarden adds the missing layer. The PreToolUse hook fires on every `Edit` / `Write` / `MultiEdit` / `NotebookEdit` and returns `ask` if `.claude/specs/active` is empty. This works regardless of which slash commands the agent has run or which templates it has filled in. The decisions log captures every edit that does land, with a backlink to the authorizing spec.

The two tools are not competing for the same surface. spec-kit operates at *prompt-construction time*: it shapes the agent's instructions before tool calls happen. specwarden operates at *tool-use time*: it intercepts tool calls the agent has already decided to make. The intervention points are orthogonal.

### When to use spec-kit alongside specwarden

The natural pairing:

1. Use spec-kit's `/speckit.specify` / `/speckit.plan` / `/speckit.tasks` commands to walk through requirements with Claude.
2. Save the resulting spec to `.claude/specs/<id>.md` and set `.claude/specs/active` to point at it (the specwarden CLI does this in one step: `specwarden activate <id>`).
3. Let Claude implement. specwarden's hooks log every edit to the decisions log; specwarden's prepare-commit-msg hook adds the `Spec: <id>` trailer.
4. Run `specwarden coverage` over the resulting commits to confirm every change traces back to an authorized spec.

spec-kit gives you the methodology and the writing experience for the spec itself. specwarden gives you the mechanical guarantee that the spec is not ignored during implementation. Use both.

### When to pick spec-kit only

- You want spec-driven development across 30+ AI agent hosts (specwarden's hook layer is Claude Code only).
- You prefer prompt-level guidance and trust the model to honor it (the eval at `evals/results/2026-05-11.md` shows that a capable model often does — but it is at the model's discretion).
- You do not need an audit trail of which spec authorized which edit.

### When to pick specwarden only

- You want filesystem-level enforcement, not prompt-level guidance.
- You want a per-commit audit trail (`specwarden trace <sha>`) and coverage reporting (`specwarden coverage`).
- Your team is on Claude Code and the cross-host portability is not load-bearing.

---

## Karpathy CLAUDE.md (`forrestchang/andrej-karpathy-skills`)

### What it is

A set of behavioral rules for Claude Code expressed as a markdown file (`CLAUDE.md`) placed in the project root or user config directory. Claude Code loads the file into the model's context at session start. The rules describe how the model should behave: ask before assuming, surface trade-offs before implementing, avoid scope creep. The original reached 110K+ stars by articulating four failure modes (silent assumptions, hidden confusion, missing trade-off surfacing, over-eager scope expansion) that most engineers had experienced.

### What it shares with specwarden

Both target the same problem: AI agents that run ahead of stated intent and produce hard-to-review diffs. Both use markdown files that Claude Code reads. The specwarden `SKILL.md` is a direct descendant of the CLAUDE.md pattern — it is read into context and shapes model behavior before any hook fires.

### What is different

The CLAUDE.md approach is purely advisory. The model reads the rules and may follow them. There is no enforcement mechanism; a model under instruction-following pressure, or a weaker model, or one that is mid-session and has lost context, can ignore the rules silently.

specwarden adds a mechanical layer. The PreToolUse hook checks `.claude/specs/active` before every edit. If no spec is active, the edit is blocked regardless of whether the model "remembered" to follow the CLAUDE.md rules. The decisions log is written by the PostToolUse hook regardless of whether the model chose to log anything.

The eval (`evals/results/2026-05-11.md`) confirmed that in a headless benchmark with a capable model, arm B (skill only, no hooks) and arm C (skill + hooks) behaved identically — the skill alone was sufficient for self-restraint. This is not a reason to skip the hooks; it is a property of the specific model and prompt combination used. The hooks exist for the tail: sessions where advisory fails.

### When to pick Karpathy CLAUDE.md over specwarden

- You want zero tooling overhead. No CLI to install, no settings.json to maintain.
- Your workflow is mostly exploratory (writing docs, answering questions) rather than code editing.
- You are satisfied with behavioral guidance and do not need enforcement or audit trails.
- You use an agent host that does not support Claude Code-style hooks (Cursor, Codex CLI without hook support).

### When to pick specwarden

- You want a permanent record of every edit and the spec that authorized it.
- You want mechanical enforcement: edits blocked until a spec exists.
- You run coverage reports over commits (`specwarden coverage`).
- You need to audit a commit's lineage (`specwarden trace <sha>`).

The two are not mutually exclusive. A project can have both a `CLAUDE.md` with behavioral rules and specwarden wired for enforcement. They operate on different surfaces.

---

## Cursor `.cursorrules`

### What it is

A per-project file (`.cursorrules`) that Cursor reads and injects into the context of AI interactions. Functionally similar to `CLAUDE.md`: plain text or markdown rules that the model is expected to follow during code generation. Cursor-specific; not portable to Claude Code, Codex CLI, or other agent hosts without re-implementation.

### What it shares with specwarden

Both are per-project configuration that shapes agent behavior. Both are committed to the repo and version-controlled.

### What is different

`.cursorrules` is advisory only — same limitation as CLAUDE.md. No hook enforcement mechanism. No decisions log. No spec lifecycle (create, activate, complete). No coverage reporting.

`.cursorrules` is also Cursor-specific. A team that uses both Cursor and Claude Code would need to maintain parallel rule files. specwarden's `SKILL.md` format is designed to be portable: the `---` frontmatter header and slash command structure are recognized by Claude Code, and the behavioral text is readable by any model even without native skill support.

### When to pick `.cursorrules` over specwarden

- Your team uses Cursor exclusively.
- You want rules to apply to all AI interactions in Cursor, not just filesystem edits.
- You have existing `.cursorrules` content and do not want to migrate to a spec-per-feature model.

### When to pick specwarden

- You use Claude Code (or want portability across agent hosts).
- You want per-feature specs rather than project-wide behavioral rules.
- You want enforcement, not just guidance.

---

## MCP servers

### What they are

The Model Context Protocol (MCP) defines a standard interface for giving AI models access to external tools and resources. An MCP server exposes tools (callable functions) and resources (readable data). Claude Code can connect to MCP servers configured in `settings.json`; the model can call MCP tools during a session the same way it calls built-in tools like `Edit` or `Bash`.

### What they share with specwarden

MCP servers and specwarden hooks both extend Claude Code's capabilities beyond the built-in tool set. Both are configured in `.claude/settings.json`. Both run as external processes.

### What is different

MCP servers are tool providers: they give the model new capabilities to call. specwarden hooks are lifecycle interceptors: they observe and gate tool calls the model was already going to make. The two concepts are orthogonal.

An MCP server could, in principle, expose a "create spec" tool and a "check active spec" tool. But an MCP tool can only be called when the model chooses to call it. The model could choose not to call "check active spec" before editing. A PreToolUse hook fires unconditionally on every edit, with no model cooperation required.

specwarden does not provide an MCP server. It does not need one for its core function.

### When to use MCP servers alongside specwarden

MCP servers are the right choice when you want to give the model access to external systems: search, databases, APIs, file indexing. They are not a replacement for lifecycle enforcement. A project that uses specwarden for spec discipline and MCP servers for tool access is using both correctly.

---

## Other Claude Code skills (e.g. Caveman)

### What they are

A growing set of community Claude Code skills target single behavioral disciplines: response style, verbosity, tool selection, refactor scope, and so on. Caveman is one example often cited in this category. Each ships as a `SKILL.md` (sometimes with companion hooks) that registers in `.claude/settings.json` alongside any other skills the user has installed.

This section does not attempt to summarize any specific peer skill's behavior or adoption — those move quickly and are better read from each project's own repository.

### What they share with specwarden

A `SKILL.md` plus optional hook scripts is the common shape. Each one tends to pick a single discipline and enforce it narrowly rather than attempting a general-purpose configuration. Multiple skills can coexist in one Claude Code session; their hooks run independently on matching tool events.

### What is different

specwarden's discipline is pre-edit workflow gating: requiring a written spec before filesystem edits land, and recording every edit with a backlink to the spec that authorized it. The disciplines other skills enforce (style, verbosity, scope guardrails) operate at different points in the agent interaction and address different failure modes.

### When to use both

A Claude Code session can register multiple skills simultaneously. Their hooks are listed independently in `.claude/settings.json` and run on the events they match. specwarden does not conflict with skills that target response style, tool selection, or other non-overlapping behaviors.

---

## Summary table

| | Advisory text | Edit enforcement | Decisions log | Coverage report | Spec lifecycle | Portable |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| GitHub Spec Kit | yes (templates) | no | no | no | yes (CLI) | 30+ agent hosts |
| Karpathy CLAUDE.md | yes | no | no | no | no | yes (any host) |
| Cursor `.cursorrules` | yes | no | no | no | no | Cursor only |
| MCP server | no* | no | no | no | no | yes |
| specwarden | yes | yes (edits) | yes | yes | yes | Claude Code + |

\* MCP servers provide tools the model can call; they are not advisory in the CLAUDE.md sense. The "no" reflects that they do not inject rules into model context.

The "portable" column for specwarden notes "Claude Code +" because the `SKILL.md` format and behavioral text work in any host that supports skill injection, even without native hook support (though without hooks the enforcement layer is absent).
