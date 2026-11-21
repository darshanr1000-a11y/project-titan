#!/usr/bin/env python3
"""Build the Voyager 1 short: Ken Burns stills + Piper narration + earshot drone, via ffmpeg.

  build.py WORKDIR     WORKDIR holds img/1..6.*, vo/1..9.wav, drone.wav, pad.wav (see README.md)
Writes WORKDIR/voyager.mp4 (1920x1080, 30 fps).
"""
import glob, os, random, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS, XF = 1920, 1080, 30, 0.8          # XF = crossfade seconds between scenes
LEAD, TAIL = 0.5, 0.7                         # silence before / after each line inside its scene
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"

# (image, narration line no., zoom direction, big title or None)
SCENES = [
    ("img/1", 1, "in", None),
    ("img/2", 2, "out", "VOYAGER 1"),
    ("img/3", 3, "in", None),
    ("img/4", 4, "in", None),
    ("img/5", 5, "in", None),
    ("stars", 6, "out", None),
    ("stars2", 7, "in", None),
    ("img/6", 8, "out", None),
    ("record", 9, "in", None),
    ("stars", None, "out", "VOYAGER 1\nLaunched 5 September 1977"),   # end card, music only
]


def run(*cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def dur(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", path]))


def starfield(path, seed):
    rnd = random.Random(seed)
    im = Image.new("RGB", (W * 2, H * 2), (3, 4, 10))
    d = ImageDraw.Draw(im)
    # faint diagonal band of haze, like the Milky Way
    for _ in range(900):
        t = rnd.random()
        x, y = int(t * W * 2), int((0.25 + 0.5 * t) * H * 2 + rnd.gauss(0, H * 0.25))
        r = rnd.randint(40, 140)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(14, 14, 26))
    im = im.filter(ImageFilter.GaussianBlur(60))
    d = ImageDraw.Draw(im)
    # sizes are at 2x, so a star must be >= 3 px to survive the downscale
    for _ in range(3200):
        x, y, r = rnd.randrange(W * 2), rnd.randrange(H * 2), rnd.choice([3, 3, 3, 4, 4, 5, 7])
        c = rnd.randint(150, 255)
        d.ellipse([x, y, x + r, y + r], fill=(c, c, min(255, c + 25)))
    glow = im.filter(ImageFilter.GaussianBlur(4))
    im = Image.blend(im, glow, 0.35).point(lambda v: min(255, int(v * 1.25)))
    im.save(path)


def record(path):
    """A drawn stand-in for the golden record (a graphic, not the NASA photo)."""
    im = Image.open(path.replace("record", "stars")).copy()
    d = ImageDraw.Draw(im)
    cx, cy, R = im.width // 2, im.height // 2, int(im.height * 0.36)
    for i, r in enumerate(range(R, int(R * 0.18), -4)):
        g = 118 + (i * 23) % 26          # fine alternating grooves, dull brass
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(g + 52, g + 18, 34))
    d.ellipse([cx - R // 6, cy - R // 6, cx + R // 6, cy + R // 6], fill=(176, 136, 58))
    # soft diagonal sheen
    sheen = Image.new("L", im.size, 0)
    ImageDraw.Draw(sheen).pieslice([cx - R, cy - R, cx + R, cy + R], 200, 240, fill=70)
    im = Image.composite(Image.new("RGB", im.size, (255, 236, 190)), im, sheen.filter(ImageFilter.GaussianBlur(30)))
    d = ImageDraw.Draw(im)
    d.ellipse([cx - 14, cy - 14, cx + 14, cy + 14], fill=(5, 5, 8))
    im.save(path)


def frame(src, out):
    """Fit any still into 2x 16:9 over a blurred fill of itself, so portrait images keep their framing."""
    im = Image.open(src).convert("RGB")
    bw, bh = W * 2, H * 2
    bg = im.resize((bw, bh)).filter(ImageFilter.GaussianBlur(40)).point(lambda v: v * 0.45)
    s = min(bw / im.width, bh / im.height) * 0.94
    fg = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    bg.paste(fg, ((bw - fg.width) // 2, (bh - fg.height) // 2))
    bg.save(out)


def title_png(text, out):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    lines = text.split("\n")
    sizes = [110] + [44] * (len(lines) - 1)
    # one-line titles sit in the lower third so they don't cover the subject; end cards are centred
    y = int(H * 0.74) if len(lines) == 1 else H // 2 - sum(sizes) // 2 - 20
    for line, sz in zip(lines, sizes):
        f = ImageFont.truetype(FONT, sz)
        w = d.textlength(line, font=f)
        d.text(((W - w) / 2 + 3, y + 3), line, font=f, fill=(0, 0, 0, 180))
        d.text(((W - w) / 2, y), line, font=f, fill=(245, 240, 225, 255))
        y += int(sz * 1.35)
    im.save(out)


def scene_clip(i, still, seconds, zoom, title, out):
    n = int(seconds * FPS)
    z = f"1+0.12*on/{n}" if zoom == "in" else f"1.12-0.12*on/{n}"
    vf = (f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s={W}x{H}:fps={FPS},"
          f"format=yuv420p")
    cmd = ["ffmpeg", "-y", "-loop", "1", "-i", still]
    if title:
        t = f"_title{i}.png"
        title_png(title, t)
        # -loop: a single-frame input would hold its faded-out (transparent) first frame forever
        cmd += ["-loop", "1", "-i", t, "-filter_complex", f"[0]{vf}[v];[1]format=rgba,fade=in:st=0.3:d=0.8:alpha=1[t];[v][t]overlay[o]",
                "-map", "[o]"]
    else:
        cmd += ["-vf", vf]
    run(*cmd, "-frames:v", str(n), "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", out)


def main(work):
    os.chdir(work)
    starfield("stars.png", 1)
    starfield("stars2.png", 2)
    if not glob.glob("img/7.*"):
        record("record.png")
    stills = {"stars": "stars.png", "stars2": "stars2.png",
              "record": (glob.glob("img/7.*") or ["record.png"])[0]}

    clips, vo_at, t = [], [], 0.0
    for i, (img, line, zoom, title) in enumerate(SCENES):
        src = stills.get(img) or glob.glob(img + ".*")[0]
        framed = f"_f{i}.png"
        if src.startswith("img/"):
            frame(src, framed)          # downloaded photo: fit over a blurred fill
        else:
            framed = src                # generated art is already 2x 16:9
        seconds = (LEAD + dur(f"vo/{line}.wav") + TAIL) if line else 4.0
        seconds += XF  # the next scene's crossfade eats into this one
        clip = f"_c{i}.mp4"
        scene_clip(i, framed, seconds, zoom, title, clip)
        clips.append((clip, seconds))
        if line:
            vo_at.append((f"vo/{line}.wav", t + LEAD))
        t += seconds - XF
    total = t + XF

    # video: chain xfades
    inputs, fc, prev, off = [], [], "[0:v]", 0.0
    for k, (c, s) in enumerate(clips):
        inputs += ["-i", c]
    for k in range(1, len(clips)):
        off += clips[k - 1][1] - XF
        fc.append(f"{prev}[{k}:v]xfade=transition=fade:duration={XF}:offset={off:.3f}[v{k}]")
        prev = f"[v{k}]"
    fc.append(f"{prev}fade=in:st=0:d=0.6,fade=out:st={total - 1.2:.3f}:d=1.2[vout]")
    run("ffmpeg", "-y", *inputs, "-filter_complex", ";".join(fc), "-map", "[vout]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "_video.mp4")

    # audio: narration placed at its scene, drone bed looped under it and ducked, pad on the record + end card
    ai, af = [], []
    for k, (wav, at) in enumerate(vo_at):
        ai += ["-i", wav]
        af.append(f"[{k}]adelay={int(at * 1000)}:all=1[n{k}]")
    nv = len(vo_at)
    af.append("".join(f"[n{k}]" for k in range(nv)) + f"amix=inputs={nv}:normalize=0,apad,atrim=0:{total:.3f}[vo]")
    ai += ["-stream_loop", "-1", "-i", "drone.wav", "-stream_loop", "-1", "-i", "pad.wav"]
    pad_at = vo_at[-1][1] - LEAD
    af.append(f"[{nv}]atrim=0:{total:.3f},volume=0.55,afade=in:d=2,afade=out:st={total - 3:.3f}:d=3[bed]")
    af.append(f"[{nv + 1}]atrim=0:{total - pad_at:.3f},volume=0.35,afade=in:d=2.5,"
              f"afade=out:st={total - pad_at - 2.5:.3f}:d=2.5,adelay={int(pad_at * 1000)}:all=1[pad]")
    af.append("[vo]asplit[vo1][vo2]")
    af.append("[bed][vo1]sidechaincompress=threshold=0.03:ratio=6:attack=80:release=600[duck]")
    af.append("[duck][pad][vo2]amix=inputs=3:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11[aout]")
    run("ffmpeg", "-y", *ai, "-filter_complex", ";".join(af), "-map", "[aout]", "-t", f"{total:.3f}",
        "-ar", "48000", "-c:a", "aac", "-b:a", "192k", "_audio.m4a")

    run("ffmpeg", "-y", "-i", "_video.mp4", "-i", "_audio.m4a", "-c", "copy", "-shortest",
        "-movflags", "+faststart", "voyager.mp4")
    print(f"voyager.mp4  {total:.1f}s  scenes={len(clips)}")


if __name__ == "__main__":
    main(sys.argv[1])
