---
name: self-critique
description: Bounded review-and-fix loop for any output before declaring it done - code, research reports, video analyses, plans. Finds factual, logical, technical and quality problems against a checklist, fixes them, re-checks, and stops after at most 2 revision rounds. Use before finishing important work, when the user says "check your work", "review this", "verify", or after a deep-research report.
---

# Self-critique (bounded reflection)

Concepts are taken from the LangGraph Reflection, Reflexion and Corrective-RAG examples (MIT). The frameworks are not used.
The key ideas: critique against **external evidence** (tests, sources, transcripts), not just re-reading, and keep a hard stop.

## Loop

```
round = 0
draft → CRITIQUE → issues?
          no  → deliver
          yes → FIX the blocking issues → round += 1 → if round == 2: deliver with open issues listed
```

- **Max 2 revision rounds.** After that, list what is still open. Never loop "until perfect".
- Each round must use new evidence (run a test, open a source, re-read the transcript). A critique that only
  re-reads your own text catches style, not truth.
- Classify issues: **blocking** (wrong, unsupported, broken, unsafe) and **minor** (style, polish). Fix blocking
  issues only. Mention minor ones in a line.
- If a critique round finds nothing blocking, stop, even in round 0.

## Checklists (pick the profile)

**code**
- [ ] Tests / build actually run and pass. Paste the command and result. "Should work" doesn't count.
- [ ] Every caller of a changed function still works (grep them).
- [ ] Edge cases: empty, missing, huge, malformed input. Errors are not swallowed.
- [ ] No secrets, no destructive operations, no unasked-for scope.

**research** (verification pass after `deep-research` or any web research)
1. Extract the 5-15 claims the conclusion depends on.
2. For each claim record: sources, whether they are **independent** (different original origin. Three articles
   citing one press release count as one), publication date, primary vs secondary, fact vs opinion.
3. Rate: `verified` (2+ independent sources, or 1 primary authoritative source) · `single-source` · `contested`
   (sources disagree. Report both sides) · `unsupported` (no source found → remove or mark).
4. For important claims, target 3 independent sources where practical.
5. Gap rule: if a load-bearing claim is single-source or unsupported, do **one** targeted re-search round
   for it (counts as a revision round).
6. Add a "Verification" table to the report: claim · rating · sources · date checked.

**content** (video analyses, scripts, trend reports)
- [ ] Every timestamp exists in the transcript or chapters.
- [ ] Every visual/audio claim is backed by frames or audio actually examined, otherwise marked "not verified".
- [ ] "Why it worked" claims are labelled hypotheses.
- [ ] Ideas are original: no reuse of a creator's script, phrasing or scene sequence.

**plan**
- [ ] Each step has a verifiable done-check.
- [ ] Dependencies are ordered. Independent steps are marked parallelisable.
- [ ] Risky / irreversible steps are flagged for user approval.

## Output

Append a short block to the deliverable (or the final message):

```
Self-critique: <rounds> round(s). Fixed: <n blocking>. Open: <list or "none">. Evidence used: <tests/sources/...>
```

## Optional independent critic

For high-stakes output, run the critique in a fresh subagent (Agent tool, general-purpose) given only the
deliverable, the checklist and the evidence paths. A fresh context does not share your blind spots. Skip this for
routine work. It roughly doubles the cost.
