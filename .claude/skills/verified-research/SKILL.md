---
name: verified-research
description: Research a topic with an explicit verification loop - plan, search multiple sources in parallel, then verify load-bearing claims for independent sourcing, dates and contradictions, re-search the gaps once, and deliver a cited report with a verification table. Use when accuracy matters - "research and verify", "fact-check", "deep dive with sources", research that will drive a decision or a video script.
---

# Verified research

Two existing pieces, in order. Don't rebuild either.

1. **Gather:** run the `anthropic-skills:deep-research` skill (parallel researcher subagents → report writer).
   Add these constraints to every researcher prompt:
   - prefer original/primary sources, and record each source's publication date
   - label each item fact / statistic / opinion
   - record which original source a secondary article relies on, so independence can be judged later
   - for time-sensitive topics, state the "as of" date

2. **Verify:** run `self-critique` with the **research** profile on the draft report. It extracts the
   load-bearing claims, rates each `verified / single-source / contested / unsupported` on *independent* sources,
   does one targeted re-search round for weak load-bearing claims, then appends a Verification table.

3. **Deliver:** the report plus its Verification table. Put contradictions in their own section with both sides
   cited. Remove unsupported claims or label them clearly. Never fill a gap with a plausible-sounding number.

When the subagent tool is unavailable, do steps 1-2 yourself: plan 3-5 sub-questions, search each, keep
notes as `claim — source (date, primary?)`, then verify the same way.
