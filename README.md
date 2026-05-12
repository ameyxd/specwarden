# spec-trace 🪨

Every code change traces back to a written spec. Enforced by hooks, not vibes.

![demo](docs/assets/demo.gif)

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/ameyxd/spec-trace/main/install.sh)
```

---

## The problem

AI agents start editing the moment you say go. Silent assumptions get baked in,
adjacent files get touched, and by the time you review the diff the decisions
are already made. The [Karpathy CLAUDE.md](https://github.com/forrestchang/andrej-karpathy-skills)
named the failure modes — silent assumptions, hidden confusion, scope creep — and
proposed behavioral rules as the cure. Rules work until the agent ignores them.

## The fix in 30 seconds

A typical session with spec-trace active:

```
You:    add JWT auth to the Flask API

Claude: I've drafted the spec at .claude/specs/jwt-auth.md — here's a summary
        so you can review before I touch any files:

        ## Assumptions
        - The app uses Flask-Login; we are not replacing it
        - Secret is sourced from env var JWT_SECRET; wiring that var is out of scope

        ## Scope
        - Modify src/auth/middleware.py
        - Add src/auth/jwt.py
        - Leave src/models/user.py untouched

        ## Non-goals
        - No refresh token logic
        - No env-var wiring for JWT_SECRET

        ## Success criteria
        - [ ] test_jwt_verify passes
        - [ ] Manual login with expired token returns 401

        Type `ready` when you want me to proceed.

You:    ready

Claude: [edits src/auth/middleware.py]
        [creates src/auth/jwt.py]

# .claude/decisions/jwt-auth.md now contains:
## 2026-05-06T14:32:18Z
- File: src/auth/jwt.py
- Lines: 1–87 (created)
- Summary: Initial JWT verification middleware
- Tool: Write
```

No edits land until the spec exists. Every edit that does land is logged.

## Benchmark numbers

Across five fixture tasks, arm A (vanilla Claude Code) modified **8 files** in
total. With spec-trace in context, arm B (skill only) and arm C (skill + hooks)
modified **2 and 1 files** respectively — a 75–87% reduction in out-of-scope
file modifications.

**Honest caveat:** in headless mode, the skill text alone caused Claude to draft
a spec and halt, waiting for human `ready` confirmation that the runner never
sent. Arms B and C behaved nearly identically in this benchmark because the
PreToolUse hook never had a chance to fire — Claude self-restrained before
attempting any edit. The enforcement value of arm C is in the tail: sessions
where a capable model would otherwise skip the advisory. Total run cost: $3.41.

Full methodology, scorecard, and raw session logs: [evals/results/2026-05-11.md](evals/results/2026-05-11.md).
Reproduce with `make eval` (~15 min, ~$3.50 in API tokens).

## Install and first spec

**macOS / Linux / WSL:**
```bash
bash <(curl -fsSL https://raw.githubusercontent.com/ameyxd/spec-trace/main/install.sh)
```

**Windows PowerShell:**
```powershell
irm https://raw.githubusercontent.com/ameyxd/spec-trace/main/install.ps1 | iex
```

Both installers run `pipx install spec-trace` and `spec-trace init` in the
current directory. If you prefer to do it manually:

```bash
pipx install spec-trace
cd your-repo
spec-trace init      # creates .claude/specs/, wires hooks into .claude/settings.json
```

**Create your first spec:**
```bash
spec-trace new "add jwt auth"
# opens .claude/specs/2026-05-06_add-jwt-auth.md in $EDITOR
# fill in the four sections, then:
spec-trace activate 2026-05-06_add-jwt-auth
```

Now open Claude Code. The PreToolUse hook is live; no edit lands until the spec
is active.

---

## Architecture

Three pieces: a CLI that manages spec state, hooks that intercept every edit,
and a skill that loads the four-slash-command interface into the model's context.
Removing the skill leaves enforcement intact; removing the hooks leaves advisory
guidance intact; the CLI manages the `.claude/specs/active` file that both read.
Full detail: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## What spec-trace is not

Pulled from the [project spec](SPEC_spec-trace.md) and the [philosophy doc](docs/PHILOSOPHY.md):

- Not a project management tool. No assignees, priorities, due dates, or status boards.
- Not a multi-user collaboration tool. Single-developer workflow only in v1.
- Not a spec generator. The human writes the spec; that is the forcing function.
- Not an integration layer. No GitHub Issues, Linear, Jira, or other trackers.
- Not a migration tool. No importer for existing `.cursorrules` or `CLAUDE.md` rules.
- Not a web UI. Everything is markdown files in git.

## Comparison

| | Advisory text | Edit enforcement | Decisions log | Coverage report | Portable |
|---|:---:|:---:|:---:|:---:|:---:|
| Karpathy CLAUDE.md | yes | no | no | no | any host |
| Cursor `.cursorrules` | yes | no | no | no | Cursor only |
| MCP server | — | no | no | no | yes |
| spec-trace | yes | yes | yes | yes | Claude Code + |

Long-form comparison with tradeoffs: [docs/COMPARISONS.md](docs/COMPARISONS.md).

## FAQ

**Doesn't this slow me down?**
It adds one step — writing a four-section spec — before code lands. That step
is roughly three to five minutes for a focused change. The bet is that surfacing
assumptions and scope before editing saves more time in review and debugging than
the spec took to write. For cases where it genuinely is overhead (typo fix,
dependency bump), set `SPEC_TRACE_QUICKFIX=1` to bypass the check.

**What about quick fixes?**
`SPEC_TRACE_QUICKFIX=1 claude` skips the PreToolUse check entirely. The
decisions log is not populated and the commit will appear as uncovered in
`spec-trace coverage` output. Use it for edits where a spec would be absurd;
accept the uncovered commit.

**Why not just use GitHub Issues?**
Issues track what you want to do. Specs record what you assumed, what was
explicitly out of scope, and how you knew you were done — before the code was
written, not after. The decisions log records what the agent actually did and
why. That chain is what lets you audit a commit six months later without reading
every line of diff. An issue link in a commit message does not give you that.

**Does it work with Cursor or Codex CLI?**
The `SKILL.md` format and behavioral text load correctly in any agent host that
supports skill injection or system-prompt files. Without Claude Code's hook
support, the enforcement layer (PreToolUse block) is absent, and you get the
advisory behavior only — equivalent to arm B in the benchmark.

## Contributing

The most useful contribution is a new eval fixture: a small self-contained
coding task with a `starting_state/` directory and a `prompt.md`. See
[evals/README.md](evals/README.md) for the fixture format and the submission
checklist. Bug fixes and tests follow the same path: open an issue, reference it
in a spec, submit a PR. Commits follow [Conventional Commits](https://www.conventionalcommits.org/)
(`feat:`, `fix:`, `docs:`, `test:`, `chore:`, `refactor:`); subject under 72
characters; no emoji.

## License

MIT — see [LICENSE](LICENSE).
