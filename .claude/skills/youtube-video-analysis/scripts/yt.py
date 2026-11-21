#!/usr/bin/env python3
"""Collect evidence about a YouTube video or a channel/search listing, as JSON.

  yt.py video URL [--transcript FILE] [--lang en] [--section-sec 60]
  yt.py listing (@handle | channel URL | "search:QUERY") [--limit 30]
  yt.py --self-check

Backends, tried in order, each optional:
  video metadata : yt-dlp  ->  YouTube oEmbed (stdlib, title/channel/thumbnail only)
  transcript     : --transcript FILE (.vtt/.srt/.json)  ->  youtube-transcript-api  ->  yt-dlp subtitles
The output's "evidence" block says exactly which sources succeeded, so the
report never claims more than was actually retrieved.
"""
import argparse, json, re, sys, urllib.parse, urllib.request

ID_RE = re.compile(r"(?:v=|youtu\.be/|shorts/|embed/|live/)([A-Za-z0-9_-]{11})")


def video_id(url):
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url):
        return url
    m = ID_RE.search(url)
    if not m:
        raise ValueError(f"no YouTube video id in {url!r}")
    return m.group(1)


def ts(sec):
    sec = int(sec)
    h, r = divmod(sec, 3600)
    return f"{h}:{r // 60:02d}:{r % 60:02d}" if h else f"{r // 60:02d}:{r % 60:02d}"


# ---------- transcript parsing (any backend -> [{start, dur, text}]) ----------

def _secs(t):
    t = t.replace(",", ".")
    parts = [float(p) for p in t.split(":")]
    while len(parts) < 3:
        parts.insert(0, 0.0)
    return parts[0] * 3600 + parts[1] * 60 + parts[2]


def parse_subtitles(text):
    """Parse WebVTT or SRT. Drops markup and the rolling duplicate lines auto-captions repeat."""
    cues, last = [], None
    for block in re.split(r"\n\s*\n", text.replace("\r", "")):
        m = re.search(r"([\d:.,]+)\s*-->\s*([\d:.,]+)", block)
        if not m:
            continue
        body = block[m.end():].split("\n", 1)[1] if "\n" in block[m.end():] else ""
        lines = [re.sub(r"<[^>]+>", "", l).strip() for l in body.split("\n")]
        lines = [l for l in lines if l and l != last]
        if not lines:
            continue
        last = lines[-1]
        start, end = _secs(m.group(1)), _secs(m.group(2))
        cues.append({"start": start, "dur": round(end - start, 3), "text": " ".join(lines)})
    return cues


def parse_transcript_file(path):
    raw = open(path, encoding="utf-8").read()
    if path.endswith((".vtt", ".srt")):
        return parse_subtitles(raw)
    data = json.loads(raw)
    # accept a bare list, or a wrapper such as {"transcript": [...]} from an API tool
    if isinstance(data, dict):
        data = next((v for v in data.values() if isinstance(v, list)), [])
    out = []
    for c in data:
        start = c.get("start", c.get("startMs", c.get("offset", 0)))
        if "startMs" in c:
            start = float(start) / 1000
        out.append({"start": float(start), "dur": float(c.get("dur", c.get("duration", 0)) or 0),
                    "text": str(c.get("text", "")).strip()})
    return out


def sections(cues, chapters=None, every=60):
    """Group cues by real chapters when the video has them, else fixed windows. Never invents times."""
    if not cues:
        return []
    if chapters:
        bounds = [(c["start_time"], c.get("title")) for c in chapters]
    else:
        end = cues[-1]["start"] + cues[-1]["dur"]
        bounds = [(t, None) for t in range(0, int(end) + 1, every)]
    out = []
    for i, (start, title) in enumerate(bounds):
        stop = bounds[i + 1][0] if i + 1 < len(bounds) else float("inf")
        text = " ".join(c["text"] for c in cues if start <= c["start"] < stop)
        if text:
            out.append({"start": ts(start), "chapter": title, "text": text})
    return out


def window(cues, upto):
    return " ".join(c["text"] for c in cues if c["start"] < upto)


# ---------- backends ----------

def ytdlp_info(url, flat=False, limit=None):
    import yt_dlp  # optional dependency
    opts = {"quiet": True, "skip_download": True, "no_warnings": True}
    if flat:
        opts.update(extract_flat="in_playlist", playlistend=limit)
    with yt_dlp.YoutubeDL(opts) as y:
        return y.extract_info(url, download=False)


def oembed(vid):
    q = urllib.parse.urlencode({"format": "json", "url": f"https://www.youtube.com/watch?v={vid}"})
    with urllib.request.urlopen(f"https://www.youtube.com/oembed?{q}", timeout=15) as r:
        d = json.load(r)
    return {"title": d.get("title"), "channel": d.get("author_name"),
            "channel_url": d.get("author_url"), "thumbnail": d.get("thumbnail_url")}


def transcript_api(vid, lang):
    from youtube_transcript_api import YouTubeTranscriptApi  # optional dependency
    return [{"start": s.start, "dur": s.duration, "text": s.text}
            for s in YouTubeTranscriptApi().fetch(vid, languages=[lang, "en"])]


def ytdlp_subs(info, lang):
    """Fetch a VTT track that yt-dlp already listed (manual subs preferred over auto)."""
    for key in ("subtitles", "automatic_captions"):
        for code in (lang, "en"):
            for fmt in (info.get(key) or {}).get(code, []):
                if fmt.get("ext") == "vtt":
                    with urllib.request.urlopen(fmt["url"], timeout=30) as r:
                        return parse_subtitles(r.read().decode("utf-8", "replace")), key
    return None, None


# ---------- commands ----------

def cmd_video(a):
    vid = video_id(a.url)
    url = f"https://www.youtube.com/watch?v={vid}"
    ev, errors, meta, info, cues = {}, {}, {"id": vid, "url": url}, None, None

    try:
        info = ytdlp_info(url)
        meta.update({k: info.get(k) for k in (
            "title", "channel", "channel_url", "channel_follower_count", "duration", "upload_date",
            "view_count", "like_count", "comment_count", "categories", "tags", "description",
            "thumbnail", "chapters", "is_live", "was_live")})
        meta["format"] = "short" if "/shorts/" in (info.get("webpage_url") or "") or (info.get("duration") or 999) <= 60 else "long-form"
        ev["metadata"] = "yt-dlp"
    except Exception as e:
        errors["yt-dlp"] = str(e)[:300]
        try:
            meta.update(oembed(vid))
            ev["metadata"] = "oembed (title/channel/thumbnail only; no views, duration, date)"
        except Exception as e2:
            errors["oembed"] = str(e2)[:300]

    if a.transcript:
        cues, ev["transcript"] = parse_transcript_file(a.transcript), f"file:{a.transcript}"
    else:
        try:
            cues, ev["transcript"] = transcript_api(vid, a.lang), "youtube-transcript-api"
        except Exception as e:
            errors["youtube-transcript-api"] = str(e)[:300]
            if info:
                try:
                    cues, kind = ytdlp_subs(info, a.lang)
                    if cues:
                        ev["transcript"] = f"yt-dlp {kind}"
                except Exception as e2:
                    errors["yt-dlp-subs"] = str(e2)[:300]

    ev.setdefault("metadata", None)
    ev.setdefault("transcript", None)
    ev["visual"] = None  # this script never looks at frames; see video-understand
    ev["audio"] = None
    out = {"video": meta, "evidence": ev, "errors": errors}
    if cues:
        out["hook"] = {"first_5s": window(cues, 5), "first_30s": window(cues, 30)}
        out["sections"] = sections(cues, meta.get("chapters"), a.section_sec)
        out["transcript"] = [{"t": ts(c["start"]), "text": c["text"]} for c in cues]
    json.dump(out, sys.stdout, indent=1, ensure_ascii=False)
    print()
    return 0 if (ev["metadata"] or cues) else 2


def cmd_listing(a):
    t = a.target
    if t.startswith("search:"):
        src = f"ytsearch{a.limit}:{t[7:]}"
    elif t.startswith("@"):
        src = f"https://www.youtube.com/{t}/videos"
    else:
        src = t.rstrip("/") + ("" if t.rstrip("/").endswith(("/videos", "/shorts")) else "/videos")
    info = ytdlp_info(src, flat=True, limit=a.limit)
    rows = []
    for e in (info.get("entries") or [])[: a.limit]:
        # shape matches youtube-agent-pro's yt-viral/swipe.py input
        rows.append({"channel": e.get("channel") or e.get("uploader") or info.get("channel"),
                     "title": e.get("title"), "views": e.get("view_count"),
                     "url": e.get("url") or f"https://www.youtube.com/watch?v={e.get('id')}",
                     "duration": e.get("duration"), "upload_date": e.get("upload_date")})
    json.dump(rows, sys.stdout, indent=1, ensure_ascii=False)
    print()
    return 0


def self_check():
    assert video_id("https://youtu.be/jNQXAC9IVRw?t=3") == "jNQXAC9IVRw"
    assert video_id("https://www.youtube.com/shorts/jNQXAC9IVRw") == "jNQXAC9IVRw"
    assert video_id("https://www.youtube.com/watch?app=desktop&v=jNQXAC9IVRw&t=1") == "jNQXAC9IVRw"
    assert ts(5) == "00:05" and ts(3725) == "1:02:05"
    vtt = ("WEBVTT\n\n00:00:00.000 --> 00:00:02.500\n<c>Hello</c> there\n\n"
           "00:00:02.500 --> 00:00:04.000\nHello there\nnext line\n\n"
           "00:01:05.000 --> 00:01:07.000\nlater\n")
    cues = parse_subtitles(vtt)
    assert [c["text"] for c in cues] == ["Hello there", "next line", "later"], cues
    assert window(cues, 5) == "Hello there next line"
    s = sections(cues, every=60)
    assert [x["start"] for x in s] == ["00:00", "01:00"], s
    s = sections(cues, chapters=[{"start_time": 0, "title": "Intro"}, {"start_time": 3, "title": "Body"}])
    assert [x["chapter"] for x in s] == ["Intro", "Body"] and s[1]["text"] == "later", s
    print("self-check ok")
    return 0


def main():
    if "--self-check" in sys.argv:
        return self_check()
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("video")
    v.add_argument("url")
    v.add_argument("--transcript", help="pre-fetched transcript (.vtt/.srt/.json)")
    v.add_argument("--lang", default="en")
    v.add_argument("--section-sec", type=int, default=60)
    l = sub.add_parser("listing")
    l.add_argument("target")
    l.add_argument("--limit", type=int, default=30)
    a = p.parse_args()
    return cmd_video(a) if a.cmd == "video" else cmd_listing(a)


if __name__ == "__main__":
    sys.exit(main())
