---
name: youtube-video-analysis
description: Analyze a YouTube video from its link - metadata, timestamped transcript, sections, hook, narrative structure, storytelling and pacing techniques, and reusable lessons for original content. Use when the user gives a YouTube URL and asks to analyze, break down, study, summarize or learn from a video. Every claim is labelled by evidence type (metadata / transcript / visual / audio / inference).
---

# YouTube video analysis

Collect evidence first, then analyze only what the evidence supports.

## 1. Collect

```bash
SK="<this skill's directory>"
python3 "$SK/scripts/yt.py" video "<URL>" > /tmp/yt_video.json      # add --transcript FILE if you already have one
```

`yt.py` needs `yt-dlp` and `youtube-transcript-api` for full results (install them in a venv:
`uv venv .venv && uv pip install --python .venv/bin/python yt-dlp youtube-transcript-api`, then run it with `.venv/bin/python`).
Without them it still works with oEmbed (title, channel and thumbnail only).

Read the `evidence` block before writing anything. It decides what you may claim:

| evidence | you may analyze |
|---|---|
| `metadata: yt-dlp` | title, channel, duration, date, views/likes/comments, chapters, tags, description |
| `metadata: oembed` | title, channel and thumbnail only. Say views, duration and date are unavailable |
| `transcript: ...` | what is said and when: hook, structure, open loops, pacing of the script |
| `visual: null` (always, from yt.py) | **nothing visual**. Editing, camera, on-screen text and animation are "not verified" |

**If the run fails** (YouTube bot-walls cloud/datacenter IPs, a common cause):
1. Run it on the user's own machine, where yt-dlp normally works, or
2. Ask the user to paste the transcript or upload a `.vtt`/`.srt`, then rerun with `--transcript FILE`, or
3. Paid fallback (**ask first**, it bills the user): the Composio `SCRAPECREATORS_GET_YOUTUBE_VIDEO` and
   `..._TRANSCRIPT` tools cost about $0.001 per call. Save the transcript JSON to a file and pass it with `--transcript`.
   The free Composio `YOUTUBE_GET_VIDEO_DETAILS_BATCH` (official API) gives metadata and statistics, but the user must connect it via OAuth first.

**Visual analysis (optional, only when asked or when the analysis needs it):** download a low-res copy with the
`video-download` skill (`-f "best[height<=360]"`), then run the `video-understand` skill for scene-cut keyframes,
and look at the frames. Only then may you mark production claims as `visual`.

## 2. Write the report

Save it to `reports/youtube/<video-id>-analysis.md`. Tag every analytical claim with its evidence type:
`[M]` metadata, `[T]` transcript, `[V]` visual frames you actually viewed, `[A]` audio you actually analyzed,
`[I]` your inference. Use only timestamps that appear in the transcript or chapters. Never invent one.

```markdown
# <Title> - analysis
Evidence: metadata=<source> · transcript=<source or none> · visual=<none|N frames> · audio=<none|...>

## Video information
Title · Channel · Link · Duration · Published · Views / likes / comments · Format (short / long-form / live)
(write "unavailable" for anything you could not get)

## Content summary
<accurate summary, 5-10 sentences>

## Timestamp breakdown
| Timestamp | Topic | Purpose (hook / setup / context / escalation / reveal / payoff / CTA) |

## Hook analysis
- First 5 seconds: <quote `hook.first_5s`> - what it does
- First 30 seconds: what is promised or set up
- Curiosity created / unanswered question
- Why a viewer keeps watching

## Narrative structure
Map the video onto: introduction → setup → conflict → escalation → revelations → payoff → ending.
Adapt it to the actual video. Say plainly if it is a list, tutorial or essay with no conflict arc.

## Storytelling techniques
Curiosity gaps, open loops (where opened → where closed), stakes, emotional shifts, unexpected facts,
re-engagement points, transitions, each with a timestamp and evidence tag.

## Pacing
Words per minute per section (from transcript timing), section lengths, where density rises or drops.

## Production analysis
LIMITED unless visual/audio evidence exists. List editing, visuals, animation, camera, transitions,
music, sound design, voiceover and on-screen text, marking each "verified [V]/[A]" or "not verified".

## Why it may be engaging
Ranked hypotheses, each tagged [I] with the evidence behind it. These are not proven causes.

## Reusable lessons
Techniques (not content) to apply to original work.

## Original strategy
A fresh concept that uses those techniques on a different subject or angle. Do not reuse the creator's
script, structure scene by scene, or distinctive phrasing.
```

## 3. Check before delivering

Run the `self-critique` skill (profile: content) once over the report: every timestamp exists in the transcript,
no visual claim lacks `[V]`, and no "why it worked" claim is stated as fact.

For packaging, retention or title follow-ups, hand off to the installed `youtube-agent-pro` skills
(`yt-retention`, `yt-package`, `yt-script`) rather than re-deriving them here.
