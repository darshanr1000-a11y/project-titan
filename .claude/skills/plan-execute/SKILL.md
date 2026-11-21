---
name: plan-execute
description: Plan-and-execute workflow for complex multi-step tasks - decompose the goal, choose tools, execute step by step with checks, retry or replan on failure, delegate to subagents only when it measurably helps, and finish with a verified report. Use for large or ambiguous tasks, "build X end to end", "do this whole project", or any task with 5+ dependent steps.
---

# Plan and execute

Built from the LangGraph plan-and-execute, supervisor and hierarchical-teams patterns and the AutoGen group-chat pattern,
mapped onto native Claude Code tools (TaskCreate/TaskUpdate, Agent, plan mode). No framework is needed. Claude Code already
is the executor loop.

## 1. Understand
- Restate the objective and the definition of done in one or two lines.
- Read the code or context it touches before planning. Ask the user only about decisions that change the plan.

## 2. Plan (TaskCreate)
Each task has: an action, the tool or skill it uses, a **done-check** (a command, test, file or source that proves it), and
dependencies. Keep it to 3-12 tasks. Mark irreversible or outward-facing tasks "needs approval".

## 3. Execute
For each task: set `in_progress`, do it, run its done-check, then set `completed` **only if the check passed**.

Failure handling:
| failure | action |
|---|---|
| transient (network, flaky test, rate limit) | retry once with backoff |
| wrong approach | replan: revise the remaining tasks (TaskUpdate). Do not repeat the same attempt |
| blocked (missing access, key, decision) | mark blocked, continue independent tasks, report at the end |
| same task fails 3 times | stop that branch and report. No silent workarounds |

Replan whenever a result invalidates later tasks, not on a fixed schedule.

## 4. Delegate only when it pays

Use a subagent (Agent tool) when **one** of these holds:
- **Parallel and independent:** 2+ chunks with no shared state (research subtopics, separate modules). Launch them in one message.
- **Context isolation:** a broad search or a big read whose details you don't need, only the conclusion (`Explore`).
- **Independent review:** a critic with a fresh context (see `self-critique`).

Otherwise do it yourself. Sequential, tightly coupled work (most coding) is faster and more reliable in a single agent.
Each spawn starts cold, so give it the goal, constraints, file paths and the exact output format.

Specialist mapping (existing agents and skills first):
| role | use |
|---|---|
| research | `deep-research` skill → `self-critique` (research) |
| coding | main agent; `graphify` for codebase maps |
| testing | main agent runs the tests; `code-review` / `ponytail-review` for review |
| critic | fresh general-purpose subagent with the `self-critique` checklist |
| media | `youtube-video-analysis`, `content-trend-research`, `youtube-agent-pro:*` agents |

## 5. Verify and report
Run `self-critique` (profile matching the deliverable) once. The final report covers what was done, the evidence
(commands/results), what was skipped or blocked and why, and open risks. Never report a step done that wasn't checked.
