---
name: agent-evaluation
description: Measure whether agent sessions actually worked - tool success rates, errors per tool, repeated (retried) calls, token usage, wall time and subagent share, from Claude Code's own session transcripts, plus a task-level success checklist. Use for "why did that session fail", "how many tokens did that use", "evaluate the agent", "which tools keep failing".
---

# Agent evaluation (lightweight)

Claude Code already logs every session to `~/.claude/projects/<project>/<session>.jsonl`. Mine that before
adding any tracing stack. Langfuse, AgentOps and similar tools are only worth it once Project Friday runs agents outside
Claude Code.

```bash
python3 "<this skill's dir>/scripts/agent_stats.py"                 # all sessions
python3 "<this skill's dir>/scripts/agent_stats.py" path/to/s.jsonl --json
```

Reading the numbers:
- **tool_success_rate < 0.9**: look at `per_tool`. One tool usually dominates (often Bash with a wrong path or a blocked host).
- **repeated_identical_calls**: the agent retried the same call with the same input. A loop or a no-op retry.
  Healthy sessions are near 0.
- **output tokens vs turns**: high output per turn with few tool calls means it is writing rather than checking.
- **cost**: multiply the token counts by the current model price (see the `claude-api` skill for prices). Don't guess them.

## Task-level success (what the numbers can't tell you)

For a task worth evaluating, record in `reports/evals/<date>-<task>.md`:
goal · done-check · passed? (yes/no + evidence) · failures and root cause · tool errors that mattered · tokens/time.
Over several runs this becomes a regression set: rerun the same goals after changing skills and compare the pass rate.
