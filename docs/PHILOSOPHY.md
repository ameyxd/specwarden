# Philosophy

specwarden exists because the discipline most engineers want from AI agents — write the spec before touching the code — is easy to say and hard to enforce. This document explains the problem, the design choices, and the explicit limits of what specwarden does.

## The pain points it addresses

The Karpathy CLAUDE.md (forrestchang/andrej-karpathy-skills) introduced vocabulary that spread rapidly through the field because the recognition was universal. Four recurring failure modes when working with AI agents:

**Silent assumptions.** The agent begins an implementation on the basis of an unstated understanding: which module to touch, which database schema to assume, which edge cases to ignore. The human never sees the assumption until after the code exists and the assumption turns out to be wrong.

**Hidden confusion.** The agent encounters an ambiguity mid-implementation — should this function return `None` on error or raise? — resolves it silently in one direction, and continues. The decision is never surfaced. Future maintainers see the choice but not the reasoning.

**Missing trade-off surfacing.** The fastest path to a passing test is rarely the right architecture. An agent under pressure to ship will take the path of least resistance and produce code that works but is difficult to extend. Nothing forces the trade-off onto the table where a human can evaluate it.

**Scope creep.** The agent notices something related while implementing the requested feature. It "helpfully" fixes it. Now the diff contains unreviewed changes to modules that were not in scope, the review becomes harder, and the git history no longer maps cleanly to stated intent.

These are not model flaws in the sense of being fixable with a better model. They are structural: an agent with no checkpoint between "user says go" and "agent starts editing" will run all the way to edits without pausing to surface these issues. The Karpathy CLAUDE.md addressed this with behavioral rules in markdown. That works until the agent ignores the rules.

## Why hooks, not behavioral rules

A behavioral-rules skill improves behavior on average, but not reliably. "Reliable enough in a headless benchmark with a capable model" is not the same as "reliable with a distracted user, a weaker model, or a prompt that makes shipping feel urgent." A rule that holds most of the time is a prior, not a rule, and you learn which one you had after the diff exists.

The PreToolUse hook is the backstop. When a session calls `Edit`, `Write`, `MultiEdit` or `NotebookEdit`, the hook checks `.claude/specs/active` and the spec it names. With no active spec, or one whose four sections are still unwritten, it returns a `deny` and the tool call does not run.

This is the same insight as Karpathy CLAUDE.md, but with mechanical enforcement instead of advisory text. The advisory layer (the skill) is still present — it shapes model behavior before the hook fires. The hook is the fallback for the cases where advisory is not enough.

### What the enforcement layer does and does not reach

The gate covers the four editing tools and nothing else. A file written through
`cat >`, `sed -i` or `tee` is not intercepted and not logged. Saying "the file
system literally does not accept the edit", as earlier drafts of this document
did, was wrong: it is the *tool call* that is refused. This is a guardrail
against an agent that drifts, not a sandbox against one working around you.

### What the evals actually established

`evals/results/2026-07-25.md` is the current run; `2026-05-11.md` is superseded
and its numbers are withdrawn.

The measured result is narrow: with hooks wired, 20 of 20 edit attempts were
blocked; without them, 0 of 27. That is evidence the gate holds, and nothing
more. The gated cells changed zero files because no spec was active, so they
completed no work — that is the gate working, not a tidier diff. Whether
specwarden reduces out-of-scope edits is still unmeasured.

The earlier run reported that the skill alone produced near-total self-restraint
and concluded the hooks were redundant. It could not have shown that: every arm
ran with `--bare`, which disables hooks. The behavioural finding also failed to
reproduce — no spec file was written in any cell of the re-run. The honest
position is that advisory and enforcement have not been cleanly compared, and
the case for the hook rests on the argument above rather than on a measurement.

One thing the re-run did show: an agent told *why* it was blocked stops after
one attempt, while an agent left to guess probes the gate — 5 edit attempts
against 15. The skill's measured contribution is fewer wasted retries.

## The four-section template

The spec template is the enforcement surface for human discipline. It has four sections, not three and not seven, for specific reasons.

**Assumptions** forces the engineer to enumerate what they are taking as given before writing code. Each assumption is a potential invalidation condition: if assumption 1 turns out to be false, the spec is void and must be revised before more code lands. Listing assumptions makes them reviewable. Unlisted assumptions stay invisible until they break something.

**Scope** forces a concrete, files-and-functions level description of what will change. Not "add JWT support" but "modify `src/auth/middleware.py`, add `src/auth/jwt.py`, leave `src/models/user.py` untouched." This section makes scope creep legible: if the finished diff touches files not listed here, the spec was wrong or the implementation drifted.

**Non-goals** is the most consistently underwritten section and the most important one. The point is not to list things you obviously would not do. The point is to explicitly name the temptations: the adjacent refactor you noticed, the optimization you could add, the test suite you could expand. Writing them down as non-goals makes it harder to rationalize doing them mid-implementation. It also protects reviewers: a change that avoids an explicitly listed non-goal is easier to trust than one that simply doesn't mention the adjacent refactor.

**Success criteria** forces the engineer to describe a done state that is checkable before the work starts. Not "it works" but "test `test_jwt_verify` passes," "manual login with an expired token returns 401," "the `README` section on auth is updated." Checkable criteria prevent the vague completion problem: the agent considers itself done when the code compiles; the human considers it done when three scenarios work correctly.

The template is opinionated on purpose. Engineers complain about it for the first day, then stop complaining.

## The "one template, period" choice

specwarden ships one spec template and will not add per-language variants. This is a deliberate constraint, not an oversight.

Per-language templates introduce a maintenance surface that grows with every new language added. More importantly, the discipline the template enforces is language-agnostic: assumptions, scope, non-goals, success criteria matter equally for a Python refactor and a Go microservice. Adding a "Python template" that drops Non-goals or rephrases Assumptions as "dependencies" weakens the discipline by making it optional to think about those sections.

If a specific project needs additional context in every spec — say, a database migration template for a service with a managed schema — the right approach is to document that in the project's own `CLAUDE.md` and have engineers include a migration-specific section as part of their scope or assumptions. The core four-section structure stays intact.

## What specwarden is not

These are not oversights. They are explicit non-goals from the project spec, documented here to prevent future scope creep.

**Not a project management tool.** Specs are not Jira tickets. There are no assignees, priorities, due dates, labels, or status boards. A spec is a one-page document that answers: what are we building, why, and how will we know it's done. Project tracking is a different problem.

**Not a team collaboration tool.** specwarden targets single-developer workflows in v1. Multi-user features — spec ownership, review workflows, shared coverage dashboards — are out of scope.

**Not a spec generator.** The CLI creates a spec file from a template, but it does not fill in the content. The human fills in the four sections. Auto-generating specs defeats the purpose: the forcing function is that a human has to think through assumptions, scope, non-goals, and success criteria before any code lands. If an agent generates the spec, that thinking is skipped.

**Not an integration layer.** No integration with GitHub Issues, Linear, Jira, or other trackers. Specs live in `.claude/specs/` as markdown files in git. "Files in git" is the answer to "how do I sync this across machines" and "how do I review this with my team."

**Not a migration tool.** specwarden does not offer to import existing Cursor `.cursorrules` files or existing `CLAUDE.md` behavioral rules. The migration path is: write a spec for the next piece of work you are about to start.

For comparisons with adjacent tools that do some of these things, see `docs/COMPARISONS.md`.
