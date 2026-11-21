---
name: content-trend-research
description: Research what is working in a YouTube niche - collect real channel and search listings, find outlier videos against each channel's own baseline, extract repeated formats and title patterns, spot content gaps, and turn them into original video ideas. Use for "what's trending in my niche", "what are competitors doing", "what should I make next", "find content gaps".
---

# Content trend research

This skill is the data-collection layer. The analysis lives in the installed `youtube-agent-pro` skills.
Do not duplicate them.

## 1. Collect real listings (no guessing)

```bash
YT="<project>/.claude/skills/youtube-video-analysis/scripts/yt.py"
python3 "$YT" listing @competitor1 --limit 30 > /tmp/c1.json
python3 "$YT" listing "search:<niche keywords>" --limit 30 > /tmp/search.json
jq -s add /tmp/c*.json > /tmp/collected.json
```

- Use 3-8 comparable channels plus 1-2 keyword searches. Record the collection date.
- Keep long-form and Shorts in separate files. Mixed baselines are meaningless.
- Flat listings often lack `upload_date`. Fetch dates for the top outliers with `yt.py video URL` before making
  any recency claim.
- If yt-dlp is blocked (cloud IPs), use the free Composio `YOUTUBE_LIST_CHANNEL_VIDEOS` + `YOUTUBE_GET_VIDEO_DETAILS_BATCH`
  after the user connects YouTube, or ask the user before using the paid `SCRAPECREATORS_*` tools (~$0.001/call).
- Public listings only. Never use a logged-in session or the user's cookies.

## 2. Find outliers

Run `youtube-agent-pro:yt-viral` on `collected.json` (its `swipe.py` scores each video against its own channel's median).
A 3x outlier on a small channel is a stronger signal than a big channel's average video.

## 3. Extract patterns

For the top 5-10 outliers, run `youtube-video-analysis` (transcript evidence) and tabulate:
format · length · hook type · title formula · topic angle · structure. A pattern needs **3+ independent channels**
to count as a pattern. One channel repeating itself is a channel habit.

## 4. Gaps and ideas

- Gap = audience demand (outliers, search results, comments) that recent videos answer poorly, or not at all.
- Hand the patterns to `youtube-agent-pro:yt-idea` for scored ideas and `yt-trend` for calendar timing.
- Every idea must name a pattern it borrows and what makes it original (angle, subject, format twist).
  Reject any idea that is a retelling of one specific competitor video.

## Report (`reports/trends/<niche>-<date>.md`)

Data collected (channels, counts, date) → outlier table (video, channel, multiple, link) → repeated patterns
with evidence counts → gaps → 5-10 original ideas with the pattern each borrows → limits of the data.
Separate observed numbers from inference. "Why it worked" is always a hypothesis.
