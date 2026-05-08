# SPEC: spec-trace

> Every code change traces back to a written spec. Enforced by hooks, not vibes.

**Project name:** `spec-trace`
**Repo slug:** `spec-trace` (suggest GitHub: `<your-username>/spec-trace`)
**License:** MIT
**Primary language:** Bash + Python (>=3.10) for hook scripts; pure Markdown for the skill itself
**Distribution targets:** Claude Code (primary), Cursor, Codex CLI, Windsurf (via shared skill format)
**Target build time:** one focused weekend (~14 hours of build, ~4 hours of polish + launch prep)

---

## What this is

`spec-trace` is a Claude Code skill plus a set of lifecycle hooks that enforce the discipline most engineers want from AI agents but rarely get: write the spec before writing the code, and keep a permanent record of every decision the agent made along the way.

When an engineer asks Claude Code to implement a feature, the skill activates. It refuses to let Claude touch the filesystem until a one-page spec exists in `.claude/specs/`. The spec is short by design: assumptions, scope, non-goals, success criteria, four sections, no fluff. Once the spec is in place, every edit Claude makes is appended to a `decisions.md` log with a backlink to the originating spec ID.

The result is a repository where you can run `git log` and see, for every change, the spec that authorized it and the assumptions it depended on. When a future engineer asks "why does this exist," the answer is one click away.

## Why this matters in 2026

The Karpathy CLAUDE.md (forrestchang/andrej-karpathy-skills) hit 110K+ stars by articulating four pain points: silent assumptions, hidden confusion, missing trade-off surfacing, over-eager scope expansion. That repo proposed the cure as four behavioral rules in markdown. It worked because the recognition was universal.

`spec-trace` is the next step. It takes the same insight and operationalizes it with mechanical enforcement. Not "Claude should ask before assuming." Instead: the file system literally rejects edits when no spec exists. Same recognition, with teeth.

The opening was confirmed by Caveman (5K+ stars in days, hit 10K upvotes on r/ClaudeAI): a tightly scoped skill with a real benchmark and a one-command install can land in this ecosystem if the pain it solves is felt by everyone.

## Non-goals (do NOT build these in v1)

1. A web UI. Everything runs in the terminal and in markdown files.
2. Project management features. Specs are not Jira tickets. No assignees, no priorities, no due dates. Just: what we're doing, why, and how we'll know it's done.
3. Multi-user collaboration. Single-developer workflow only. Team features come post-v1.
4. AI-generated specs. Specs are a forcing function precisely because the human writes them. Auto-generating them defeats the purpose.
5. Integration with external trackers (GitHub Issues, Linear, etc.). Out of scope for v1; tempting but distracting.
6. Custom spec templates per language or framework. One template, period.

## Architecture

Three pieces, each does one thing:

**Piece 1: the SKILL.md.** Defines four slash commands: `/spec`, `/trace`, `/coverage`, `/spec-help`. The skill description is loaded into context on session start; full content loads only when invoked. This is the user-facing entry point.

**Piece 2: the hooks.** Two hooks run inside Claude Code's lifecycle:
- `PreToolUse` on `Edit` and `Write`: checks if `.claude/specs/active` is set. If not, returns a JSON response with `permissionDecision: ask` and a message instructing Claude to invoke `/spec` first. If a spec exists, allows the edit and pipes the diff metadata to the post-hook.
- `PostToolUse` on `Edit` and `Write`: appends the change (file path, line range, brief summary) to `.claude/decisions/<active-spec-id>.md` with a timestamp.

**Piece 3: the CLI.** A `spec-trace` Python script wraps everything: `spec-trace new <slug>` creates a new spec from template, `spec-trace activate <id>` sets the active spec, `spec-trace coverage` reports what percentage of recent commits had spec coverage, `spec-trace trace <commit>` prints the full chain (commit → decisions → spec) for a given commit hash.

The `.claude/specs/active` file is the synchronization point. When set, edits are allowed and logged. When unset, edits are blocked. Simple and inspectable.

## File layout

```
spec-trace/
├── README.md                          # The published landing page
├── LICENSE
├── install.sh                         # macOS / Linux / WSL one-liner installer
├── install.ps1                        # Windows PowerShell installer
├── pyproject.toml                     # Packages the CLI as `pipx install spec-trace`
├── .claude/
│   └── skills/
│       └── spec-trace/
│           ├── SKILL.md               # Skill definition with the 4 slash commands
│           ├── scripts/
│           │   ├── new_spec.py
│           │   ├── activate_spec.py
│           │   ├── coverage.py
│           │   └── trace.py
│           └── templates/
│               ├── spec.md.template
│               └── decision_entry.md.template
├── hooks/
│   ├── pre_tool_use.py                # Gates Edit/Write
│   ├── post_tool_use.py               # Logs to decisions.md
│   └── session_start.py               # Reminds about active spec on session start
├── src/
│   └── spec_trace/
│       ├── __init__.py
│       ├── cli.py                     # Typer-based CLI entry point
│       ├── spec.py                    # Spec creation + activation logic
│       ├── decisions.py               # Decisions log writer
│       ├── coverage.py                # Coverage calculator
│       └── trace.py                   # Walks commits → decisions → specs
├── evals/
│   ├── README.md                      # How to reproduce the benchmark
│   ├── fixtures/
│   │   ├── task_001_add_auth/         # Hand-curated task: add JWT auth
│   │   │   ├── starting_state.tar.gz
│   │   │   └── prompt.md
│   │   ├── task_002_refactor_logger/
│   │   ├── task_003_add_test_suite/
│   │   ├── task_004_fix_race/
│   │   └── task_005_add_endpoint/
│   ├── run_eval.py                    # Runs all 3 arms (control / skill / skill+hooks)
│   ├── measure.py                     # Computes axes
│   └── results/
│       └── 2026-05-XX.md              # Initial published results
├── examples/
│   ├── minimal-python-cli/
│   ├── react-component/
│   └── go-microservice/
├── docs/
│   ├── PHILOSOPHY.md                  # Why spec-first, why this template
│   ├── ARCHITECTURE.md                # The three pieces, deeper
│   ├── HOOKS.md                       # Hook contracts, edge cases
│   ├── TROUBLESHOOTING.md
│   └── COMPARISONS.md                 # vs Karpathy CLAUDE.md, vs Cursor rules
└── .github/
    └── workflows/
        ├── ci.yml                     # pytest + the eval suite
        └── release.yml                # PyPI on tag push
```

Runtime layout (what gets created in user repos when spec-trace is active):

```
<user-repo>/
├── .claude/
│   ├── specs/
│   │   ├── active                     # Single line: spec ID currently active
│   │   ├── 2026-05-06_add-auth.md
│   │   ├── 2026-05-06_refactor-logger.md
│   │   └── ...
│   └── decisions/
│       ├── 2026-05-06_add-auth.md     # One file per spec, append-only log
│       └── ...
└── (the rest of the repo)
```

## Spec template (the canonical four-section format)

```markdown
# <Spec ID>: <Short Title>

**Created:** <ISO timestamp>
**Status:** active | completed | abandoned
**Author:** <human name>

## Assumptions
What we are taking as given. If any of these turns out to be false, the spec is invalid and must be revised before more code lands.

- Assumption 1
- Assumption 2

## Scope
What this change is. Concrete, files-and-functions level if possible.

- We will modify X
- We will add Y
- We will not touch Z

## Non-goals
What this change is explicitly not. The point of this section is to prevent scope creep mid-implementation.

- We will not refactor adjacent module M
- We will not change the public API of P

## Success criteria
How we will know we are done. Must be checkable.

- [ ] Test T passes
- [ ] Manual scenario S works
- [ ] Documentation D is updated
```

The template is opinionated on purpose. Engineers complain about it for the first day, then stop complaining.

## CLI surface

```bash
# Initialize spec-trace in the current repo
spec-trace init

# Create a new spec from template (opens $EDITOR)
spec-trace new add-jwt-auth

# Activate a spec (subsequent edits are gated and logged)
spec-trace activate 2026-05-06_add-jwt-auth

# Mark active spec complete
spec-trace done

# Show coverage over the last N commits
spec-trace coverage --last 50
# Output: 47/50 commits have spec coverage (94%)
#         Uncovered: <commit hashes>

# Trace a commit back to its spec and decisions
spec-trace trace abc123
# Output: spec ID, decisions log, full lineage

# Show what would happen without making changes
spec-trace status
# Output: active spec, recent decisions, coverage trend
```

## Slash command surface (inside Claude Code sessions)

`/spec <slug>` creates and activates a spec. Opens an inline template; the user fills in the four sections. Until the user types "ready", no edits are permitted.

`/trace [<commit>]` prints the full chain for a commit. Defaults to HEAD.

`/coverage [--last N]` prints coverage stats.

`/spec-help` prints a quick-reference card.

## Hook contracts

`PreToolUse` hook receives a JSON object on stdin describing the tool call. For `Edit` and `Write` calls, the hook checks `.claude/specs/active`. If empty or missing, it returns:

```json
{
  "permissionDecision": "ask",
  "message": "spec-trace: no active spec. Run /spec <slug> first to define what you're building."
}
```

If a spec is active, the hook returns `{"permissionDecision": "allow"}` and writes a pending entry to a temp file that the `PostToolUse` hook will finalize.

`PostToolUse` reads the pending entry, the actual diff that was applied, and appends a structured entry to `.claude/decisions/<spec-id>.md`:

```markdown
## 2026-05-06T14:32:18Z
- File: src/auth/jwt.py
- Lines: 1-87 (created)
- Summary: Initial JWT verification middleware
- Tool: Write
```

`SessionStart` hook prints the currently active spec (if any) at the top of the new session, plus a reminder of the four-section template if no spec is active.

## Evaluation methodology

This is the part that prevents "half-assed" perception. Three-arm benchmark, fully reproducible.

**Arms:**
- A (control): vanilla Claude Code, no spec-trace.
- B (advisory): spec-trace skill installed but hooks disabled. Tests whether mere guidance moves the needle.
- C (enforced): spec-trace skill + hooks active. The full system.

**Tasks (5 fixtures, hand-curated):**
1. Add JWT auth to an existing Flask app.
2. Refactor a tangled logger into structured logging.
3. Add a test suite to a previously untested CLI.
4. Fix a documented race condition in a small concurrent program.
5. Add a new REST endpoint that touches three existing modules.

Each task has a `starting_state.tar.gz` (the repo state to begin from) and a `prompt.md` (what the user types to Claude Code).

**Metrics measured per arm:**
- Files modified outside the user's stated scope (lower is better)
- Number of "should I also do X" interruptions (lower is better; these are interruption events that should have been resolved at spec time)
- Wall-clock time to a working solution
- Test pass rate after Claude declares done
- Token cost (input + output)
- Reviewer score on a 1-5 scale (blinded, two reviewers per arm)

**Eval runner:** `evals/run_eval.py` spawns Claude Code in headless mode against each fixture for each arm, captures the JSONL session log, and emits a results CSV. `evals/measure.py` consumes the CSV and produces a markdown scorecard.

**Honest reporting:** publish all numbers including ones that don't favor spec-trace. The goal is credibility, not marketing. If the advisory-only arm (B) performs nearly as well as enforced (C), say so; that's still a useful finding.

Run cost estimate: ~$8-15 in API tokens for a full eval run. Document this in the eval README.

## README structure (the published landing page)

The README is the launch artifact. It needs to do five things in this order:

1. **Hero section.** One-sentence value prop, animated terminal GIF (asciicast or terminalizer), one-liner install command. Above the fold, no scrolling required.
2. **The problem.** Three sentences max. The Karpathy CLAUDE.md established the vocabulary (silent assumptions, scope creep, hidden confusion). Use it. Don't reinvent terminology.
3. **The fix in 30 seconds.** A worked example: prompt → spec → diff → decisions log. Show, don't explain.
4. **Benchmark numbers.** Lead with the headline metric. "Across 5 fixture tasks, spec-trace cut out-of-scope file modifications by 74% and eliminated `should I also do X` interruptions entirely. Reproduce: `make eval`."
5. **Install + first spec.** Two commands to install, one to create the first spec.

Below the fold:
- Architecture (the three-pieces explanation)
- Comparison to Karpathy CLAUDE.md and Cursor rules
- FAQ (anticipated: "doesn't this slow me down?", "what about quick fixes?", "why not just use Issues?")
- Contributing
- License

Banned README contents: marketing-tone superlatives, hype emojis (one rock 🪨 in the hero is fine, no more), promises about future versions.

## Launch checklist

Day -3 (Wednesday before launch weekend):
- [ ] README polished, GIF recorded, install scripts tested on macOS, Linux, WSL.
- [ ] Eval results published in `evals/results/`.
- [ ] One-liner install verified on a fresh VM.
- [ ] Repository is public, license file in place.

Day 0 (Tuesday or Wednesday, 8:00 AM ET):
- [ ] Show HN post submitted. Title: `Show HN: spec-trace, force Claude Code to write the spec first`.
- [ ] First comment on HN: 3-paragraph "why I built this," with link to eval methodology and a candid statement of limitations.
- [ ] r/ClaudeAI cross-post at 9:00 AM ET. Different angle than HN: lead with the GIF, link to repo.
- [ ] r/ChatGPTCoding cross-post at 10:00 AM ET, framed as "works with Codex too via the skill format."
- [ ] Tweet thread posted, tagging accounts known to retweet AI tooling.

Day 0 + 4 hours:
- [ ] Reply to every HN comment within 30 minutes. Technically, honestly, no marketing tone.
- [ ] If HN traffic is sustained, do not double-post anywhere else; keep the focus.

Day 1:
- [ ] Submit to `awesome-claude-code`, `awesome-mcp-servers` (yes, even though it's not an MCP server, the curators sometimes accept skills), `awesome-agent-skills`.
- [ ] Write a follow-up blog post or dev.to article: "Why I added the hooks instead of just shipping the markdown." Link back to repo.

Day 7:
- [ ] First release tagged. Bug fixes from launch week incorporated.
- [ ] Twitter recap thread: "spec-trace launched 7 days ago, here's what we learned."

Day 14-30:
- [ ] One piece of content per week (a tutorial, a release note, a "spec of the week" post).
- [ ] Respond to every issue within 24 hours.

## Risks and mitigations

**Risk 1: Hooks feel paternalistic.** Engineers hate friction.
*Mitigation:* The skill ships with a `quick-fix` mode that allows up to 20 lines of edit without a spec. Document it prominently. Also: the eval results are the marketing argument. Show the data.

**Risk 2: Claude Code hook API changes.** Anthropic ships updates.
*Mitigation:* Pin the hook spec version in `SKILL.md`. Ship a CI test that exercises the hook contract against the latest published Claude Code release weekly.

**Risk 3: Cloned in a week by someone with more reach.** This is the open-lane risk.
*Mitigation:* The methodology and the eval fixtures are the moat. Anyone can copy the skill markdown. Reproducing a credible eval suite is much harder. Make sure the eval is the hero.

**Risk 4: The five fixture tasks aren't representative.**
*Mitigation:* Document the methodology candidly. Solicit fixture contributions from the community in a `CONTRIBUTING_FIXTURES.md`. Plan a v2 with 20 tasks.

## Stretch goals (post-v1)

1. `spec-trace lint`: parse all specs in a repo and warn about ones that violate the four-section discipline (missing assumptions, scope creep evidence, etc.).
2. Decision-log timeline visualization: a static HTML page showing all decisions over time, color-coded by spec.
3. Multi-repo coverage dashboard for engineering managers (carefully: this is a different product).
4. Editor integrations: VS Code extension that surfaces the active spec in the status bar.
5. `spec-trace export`: turn a completed spec + decisions into a publishable engineering retrospective.

## Out of scope for this spec, on purpose

- Migration from existing rule files (Cursor `.cursorrules`, Claude `CLAUDE.md`). Could be done; explicitly punt.
- Per-language spec templates. One template forever.
- Automated detection of "this should have been a spec." Too brittle.
- Cloud sync of specs. Files in git is the answer.

## Definition of done for v1

- [ ] All four CLI commands work and have tests.
- [ ] All four slash commands work via the skill.
- [ ] Both hooks run in real Claude Code sessions on macOS and Linux.
- [ ] Eval suite runs end-to-end and produces a reproducible scorecard.
- [ ] README is polished and includes a GIF.
- [ ] One-liner install works on macOS, Linux, WSL, Windows PowerShell.
- [ ] CI is green.
- [ ] License file present.
- [ ] Five fixture tasks are reproducible from a clean checkout.

When all boxes are checked, ship it.
