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

The initial eval (see `evals/results/2026-05-11.md`) confirmed a pattern that anyone who has shipped a behavioral-rules skill has observed: the skill improves behavior on average, but not reliably. In the benchmark, arm B (skill in context, no hooks) had Claude self-restrain in every headless trial — the text alone was sufficient. But "sufficient in a headless benchmark with a capable model" is not the same as "sufficient in production with a distracted user, a weaker model, or a prompt that makes shipping feel urgent."

The PreToolUse hook is the backstop. When a Claude Code session tries to call `Edit`, `Write`, `MultiEdit`, or `NotebookEdit`, the hook intercepts the call and checks `.claude/specs/active`. If no spec is active, the hook returns `permissionDecision: ask` and a message telling the agent to run `/spec` first. The file system literally does not accept the edit.

This is the same insight as Karpathy CLAUDE.md, but with mechanical enforcement instead of advisory text. The advisory layer (the skill) is still present — it shapes model behavior before the hook fires. The hook is the fallback for the cases where advisory is not enough.

The benchmark finding is worth stating honestly: in the current five-fixture eval, arm C (skill + hooks) was not measurably better than arm B (skill only) because Claude never attempted an edit while the skill was in context. The hooks never fired. The value of enforcement is exactly in the tail — the cases where the agent would have ignored the advisory text. That tail cannot be measured with five headless tasks against a capable model. It can be designed against by adding the hook.

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
