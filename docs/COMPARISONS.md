# Comparisons

This document compares spec-trace with tools that occupy adjacent or overlapping space. The goal is honest positioning, not advocacy.

---

## Karpathy CLAUDE.md (`forrestchang/andrej-karpathy-skills`)

### What it is

A set of behavioral rules for Claude Code expressed as a markdown file (`CLAUDE.md`) placed in the project root or user config directory. Claude Code loads the file into the model's context at session start. The rules describe how the model should behave: ask before assuming, surface trade-offs before implementing, avoid scope creep. The original reached 110K+ stars by articulating four failure modes (silent assumptions, hidden confusion, missing trade-off surfacing, over-eager scope expansion) that most engineers had experienced.

### What it shares with spec-trace

Both target the same problem: AI agents that run ahead of stated intent and produce hard-to-review diffs. Both use markdown files that Claude Code reads. The spec-trace `SKILL.md` is a direct descendant of the CLAUDE.md pattern — it is read into context and shapes model behavior before any hook fires.

### What is different

The CLAUDE.md approach is purely advisory. The model reads the rules and may follow them. There is no enforcement mechanism; a model under instruction-following pressure, or a weaker model, or one that is mid-session and has lost context, can ignore the rules silently.

spec-trace adds a mechanical layer. The PreToolUse hook checks `.claude/specs/active` before every edit. If no spec is active, the edit is blocked regardless of whether the model "remembered" to follow the CLAUDE.md rules. The decisions log is written by the PostToolUse hook regardless of whether the model chose to log anything.

The eval (`evals/results/2026-05-11.md`) confirmed that in a headless benchmark with a capable model, arm B (skill only, no hooks) and arm C (skill + hooks) behaved identically — the skill alone was sufficient for self-restraint. This is not a reason to skip the hooks; it is a property of the specific model and prompt combination used. The hooks exist for the tail: sessions where advisory fails.

### When to pick Karpathy CLAUDE.md over spec-trace

- You want zero tooling overhead. No CLI to install, no settings.json to maintain.
- Your workflow is mostly exploratory (writing docs, answering questions) rather than code editing.
- You are satisfied with behavioral guidance and do not need enforcement or audit trails.
- You use an agent host that does not support Claude Code-style hooks (Cursor, Codex CLI without hook support).

### When to pick spec-trace

- You want a permanent record of every edit and the spec that authorized it.
- You want mechanical enforcement: edits blocked until a spec exists.
- You run coverage reports over commits (`spec-trace coverage`).
- You need to audit a commit's lineage (`spec-trace trace <sha>`).

The two are not mutually exclusive. A project can have both a `CLAUDE.md` with behavioral rules and spec-trace wired for enforcement. They operate on different surfaces.

---

## Cursor `.cursorrules`

### What it is

A per-project file (`.cursorrules`) that Cursor reads and injects into the context of AI interactions. Functionally similar to `CLAUDE.md`: plain text or markdown rules that the model is expected to follow during code generation. Cursor-specific; not portable to Claude Code, Codex CLI, or other agent hosts without re-implementation.

### What it shares with spec-trace

Both are per-project configuration that shapes agent behavior. Both are committed to the repo and version-controlled.

### What is different

`.cursorrules` is advisory only — same limitation as CLAUDE.md. No hook enforcement mechanism. No decisions log. No spec lifecycle (create, activate, complete). No coverage reporting.

`.cursorrules` is also Cursor-specific. A team that uses both Cursor and Claude Code would need to maintain parallel rule files. spec-trace's `SKILL.md` format is designed to be portable: the `---` frontmatter header and slash command structure are recognized by Claude Code, and the behavioral text is readable by any model even without native skill support.

### When to pick `.cursorrules` over spec-trace

- Your team uses Cursor exclusively.
- You want rules to apply to all AI interactions in Cursor, not just filesystem edits.
- You have existing `.cursorrules` content and do not want to migrate to a spec-per-feature model.

### When to pick spec-trace

- You use Claude Code (or want portability across agent hosts).
- You want per-feature specs rather than project-wide behavioral rules.
- You want enforcement, not just guidance.

---

## MCP servers

### What they are

The Model Context Protocol (MCP) defines a standard interface for giving AI models access to external tools and resources. An MCP server exposes tools (callable functions) and resources (readable data). Claude Code can connect to MCP servers configured in `settings.json`; the model can call MCP tools during a session the same way it calls built-in tools like `Edit` or `Bash`.

### What they share with spec-trace

MCP servers and spec-trace hooks both extend Claude Code's capabilities beyond the built-in tool set. Both are configured in `.claude/settings.json`. Both run as external processes.

### What is different

MCP servers are tool providers: they give the model new capabilities to call. spec-trace hooks are lifecycle interceptors: they observe and gate tool calls the model was already going to make. The two concepts are orthogonal.

An MCP server could, in principle, expose a "create spec" tool and a "check active spec" tool. But an MCP tool can only be called when the model chooses to call it. The model could choose not to call "check active spec" before editing. A PreToolUse hook fires unconditionally on every edit, with no model cooperation required.

spec-trace does not provide an MCP server. It does not need one for its core function.

### When to use MCP servers alongside spec-trace

MCP servers are the right choice when you want to give the model access to external systems: search, databases, APIs, file indexing. They are not a replacement for lifecycle enforcement. A project that uses spec-trace for spec discipline and MCP servers for tool access is using both correctly.

---

## Caveman

### What it is

Caveman is a Claude Code skill (the project that demonstrated the "tightly scoped skill with a benchmark" launch pattern that informed spec-trace's strategy). It reached 5K+ stars quickly and hit 10K upvotes on r/ClaudeAI. Caveman is aimed at a different domain — reducing Claude Code's verbosity, enforcing a minimal response style, keeping the agent focused rather than expansive. The specific behavior it enforces is different from spec-trace's.

### What it shares with spec-trace

Both are Claude Code skills with a `SKILL.md` file. Both have a benchmark. Both are tightly scoped with a single stated purpose. Both use the "skill + hooks" pattern to go beyond advisory text.

### What is different

Caveman targets response style and verbosity. spec-trace targets pre-edit workflow discipline: requiring a written spec before filesystem edits land.

They address different layers of the same general problem (agents doing too much or behaving unexpectedly) but at different points in the interaction. Caveman shapes how Claude responds. spec-trace shapes what Claude is allowed to do.

### When to use both

They do not conflict. A project can install Caveman's skill for response discipline and spec-trace for spec enforcement simultaneously. The hooks are registered independently in `settings.json`; Claude Code runs all matching hooks per tool event.

---

## Summary table

| | Advisory text | Edit enforcement | Decisions log | Coverage report | Spec lifecycle | Portable |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Karpathy CLAUDE.md | yes | no | no | no | no | yes (any host) |
| Cursor `.cursorrules` | yes | no | no | no | no | Cursor only |
| MCP server | no* | no | no | no | no | yes |
| Caveman | yes | yes (style) | no | no | no | Claude Code |
| spec-trace | yes | yes (edits) | yes | yes | yes | Claude Code + |

\* MCP servers provide tools the model can call; they are not advisory in the CLAUDE.md sense. The "no" reflects that they do not inject rules into model context.

The "portable" column for spec-trace notes "Claude Code +" because the `SKILL.md` format and behavioral text work in any host that supports skill injection, even without native hook support (though without hooks the enforcement layer is absent).
