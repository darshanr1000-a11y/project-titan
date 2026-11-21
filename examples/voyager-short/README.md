# Voyager 1 short (56 s)

Free, local pipeline: public-domain NASA stills (Wikimedia Commons) with slow Ken Burns moves, Piper TTS narration
(`en_US-ryan-high`, offline), an earshot drone/pad bed ducked under the voice, and ffmpeg crossfades. No paid APIs.

## Rebuild

```bash
uv pip install --python .venv/bin/python piper-tts pillow
W=/path/to/workdir; mkdir -p $W/img $W/vo
# images: img/1..6 (see credits), img/7 optional (else a drawn record graphic is used)
# voice:  en_US-ryan-high.onnx(+.json) from huggingface.co/rhasspy/piper-voices
n=0; while IFS= read -r l; do n=$((n+1)); echo "$l" | .venv/bin/piper -m en_US-ryan-high.onnx --length-scale 1.12 --sentence-silence 0.35 -f $W/vo/$n.wav; done < narration.txt
earshot make --sound drone/dark -o $W/drone.wav; earshot make --sound pad/air -o $W/pad.wav
.venv/bin/python build.py $W    # -> $W/voyager.mp4
```

## Credits (all public domain, NASA, via Wikimedia Commons)
1. Titan_3E_with_Voyager_1.jpg (launch, 5 Sep 1977)
2. Voyager_spacecraft_model.png
3. Jupiter's_Great_Red_Spot_-_GPN-2003-000003.jpg (Voyager 1, 1979)
4. Solar_System_Montage_of_Voyager_Images_-_GPN-2003-000006.jpg
5. Pale_Blue_Dot.png (Voyager 1, 14 Feb 1990)
6. Voyager_Development_Test_Model_PIA21731.jpg

The starfields and the golden record are drawn by `build.py` (they are graphics, not photographs).
