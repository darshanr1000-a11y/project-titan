#!/usr/bin/env python3
"""Per-session agent metrics from Claude Code transcripts (~/.claude/projects/*/*.jsonl).

  agent_stats.py [FILE_OR_DIR ...] [--json]     default: all sessions under ~/.claude/projects
  agent_stats.py --self-check

Reports per session: turns, tool calls / errors per tool, retries (same tool+input repeated),
tokens (input, cache read/write, output), wall time, subagent (sidechain) share.
Stdlib only. Reads local files, sends nothing anywhere.
"""
import collections, glob, json, os, sys
from datetime import datetime


def _t(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def analyze(lines):
    calls, errors, seen, retries = collections.Counter(), collections.Counter(), collections.Counter(), 0
    names, tok = {}, collections.Counter()
    turns = side = 0
    first = last = None
    for raw in lines:
        try:
            d = json.loads(raw)
        except ValueError:
            continue
        t = _t(d.get("timestamp"))
        if t:
            first, last = first or t, t
        msg = d.get("message") or {}
        content = msg.get("content") if isinstance(msg.get("content"), list) else []
        if d.get("type") == "assistant":
            turns += 1
            side += bool(d.get("isSidechain"))
            u = msg.get("usage") or {}
            for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens", "output_tokens"):
                tok[k] += u.get(k) or 0
            for b in content:
                if b.get("type") == "tool_use":
                    names[b["id"]] = b["name"]
                    calls[b["name"]] += 1
                    key = (b["name"], json.dumps(b.get("input"), sort_keys=True))
                    retries += seen[key] > 0
                    seen[key] += 1
        elif d.get("type") == "user":
            for b in content:
                if b.get("type") == "tool_result" and b.get("is_error"):
                    errors[names.get(b.get("tool_use_id"), "?")] += 1
    n = sum(calls.values())
    return {
        "assistant_turns": turns, "subagent_turns": side,
        "tool_calls": n, "tool_errors": sum(errors.values()),
        "tool_success_rate": round(1 - sum(errors.values()) / n, 3) if n else None,
        "repeated_identical_calls": retries,
        "per_tool": {k: {"calls": v, "errors": errors[k]} for k, v in calls.most_common()},
        "tokens": dict(tok),
        "wall_minutes": round((last - first).total_seconds() / 60, 1) if first and last else None,
    }


def files(args):
    paths = args or [os.path.expanduser("~/.claude/projects")]
    for p in paths:
        yield from (sorted(glob.glob(os.path.join(p, "**", "*.jsonl"), recursive=True)) if os.path.isdir(p) else [p])


def self_check():
    L = [
        {"type": "assistant", "timestamp": "2026-01-01T00:00:00Z", "message": {"usage": {"input_tokens": 10, "output_tokens": 5},
         "content": [{"type": "tool_use", "id": "a", "name": "Bash", "input": {"c": "ls"}}]}},
        {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "a", "is_error": True}]}},
        {"type": "assistant", "timestamp": "2026-01-01T00:03:00Z", "isSidechain": True, "message": {"usage": {"output_tokens": 1},
         "content": [{"type": "tool_use", "id": "b", "name": "Bash", "input": {"c": "ls"}}]}},
        {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "b"}]}},
        "not json",
    ]
    r = analyze(json.dumps(x) if isinstance(x, dict) else x for x in L)
    assert r["tool_calls"] == 2 and r["tool_errors"] == 1 and r["tool_success_rate"] == 0.5, r
    assert r["repeated_identical_calls"] == 1 and r["subagent_turns"] == 1, r
    assert r["tokens"]["output_tokens"] == 6 and r["wall_minutes"] == 3.0, r
    print("self-check ok")


def main():
    a = sys.argv[1:]
    if "--self-check" in a:
        return self_check()
    as_json = "--json" in a
    out = {}
    for f in files([x for x in a if x != "--json"]):
        with open(f, encoding="utf-8", errors="replace") as fh:
            out[f] = analyze(fh)
    if as_json:
        print(json.dumps(out, indent=1))
        return
    for f, r in out.items():
        t = r["tokens"]
        print(f"{os.path.basename(f)[:40]:40} turns={r['assistant_turns']:<4} tools={r['tool_calls']:<4} "
              f"err={r['tool_errors']:<3} ok={r['tool_success_rate']} repeats={r['repeated_identical_calls']:<3} "
              f"out_tok={t.get('output_tokens', 0):<7} cache_read={t.get('cache_read_input_tokens', 0):<9} min={r['wall_minutes']}")
        worst = [(k, v) for k, v in r["per_tool"].items() if v["errors"]]
        if worst:
            print("   errors by tool:", ", ".join(f"{k} {v['errors']}/{v['calls']}" for k, v in worst))


if __name__ == "__main__":
    sys.exit(main())
