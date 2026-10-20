# Storyfilm

Make an original narrated **3–4 minute animated film at 1920×1080, 12 FPS**, using a title and brief in GitHub Actions. No API keys, paid model services, GPU or thumbnails.

[Character designs](examples/characters.png) · [Read the screenplay](examples/Depressed.md) · [Storyboard](examples/storyboard.jpg) · [Watch the sample](examples/sample.mp4)

## Make a film

1. Open **Actions → Make a film → Run workflow** on `main`.
2. Enter the title and brief.
3. Download **film-N** from the completed run's **Artifacts**. Unzip and play `film.mp4`.

To render the fully authored sample, enter:

**Title:** `Depressed`

**Brief:**
> Use the authored depression story. Male lead. An unanswered message, an honest sentence in a notebook, a short walk, and the decision to ask for support. A beginning rather than an instant recovery.

This exact phrase selects the included 496-word screenplay. Change **Male lead** to **Female lead** for the version with the female protagonist. This sample has a deliberate story arc and runs **3:30**. Selecting it uses the included plot; the rest of the brief does not rewrite that plot.

For a **different story**, omit “authored depression story” and “sample: depressed”. The local AI writer follows your brief. Example:

**Title:** `The Unfinished Page`

**Brief:**
> Female lead. She sits at her desk, unable to finish a letter she has avoided for weeks. She crosses out the first sentence and puts the pen down. She walks along a quiet street, thinking about what she is afraid to admit. She sits on a park bench and opens the unfinished letter on her phone. Back at her desk, she writes a simpler, more honest version. End with her sending it, still uncertain about the answer. Quiet and specific, with a restrained hopeful ending.

Use 4–8 clear chronological events with an obstacle, a choice and an ending. Include **she / female lead** or **he / male lead**. One adult protagonist appears throughout. The male lead is bald; the female lead has a dark bob hairstyle. They are original designs inspired by the broad expressive 2D format, without copied assets.

## Current renderer

- Rebuilt characters: rounded heads, thick articulated limbs, clothed bodies, shading, hands, shoes and clearly exposed, shaded necks. Heads pivot at the jaw rather than floating above the collar. The female has hair.
- Larger expressive eyes, worried/sad/tired/determined expressions, pupils, blinks, tears, head tilts, breathing and gestures.
- Bedroom, desk, street, park, gym and rooftop rebuilt with furniture, windows, plants, perspective, lighting and distinct night/dawn palettes.
- Seated poses aligned to the bench; foreground desk occlusion; phone grips, thumb scrolling, writing hands, and alternating walk cycles.
- Locked establishing and medium shots, with one deliberate cut per beat; no continuous zoom drift. Phone and notebook inserts show typing, sending and writing. Captions remain sharp at output resolution.
- All drawing paths rasterized directly at **1920×1080**, rather than enlarging 540p frames. Playback defaults to **12 FPS**.
- A complete authored depression story, plus a larger local **Qwen3-4B-Instruct-2507 Q4_K_M** writer for other stories. The writer sees the whole plot and writes three connected acts, retaining prior narration for continuity. Obvious action mismatches trigger a targeted repair; valid acts are checkpointed for local retries.
- Twelve story beats, approximately 390–600 words. Production targets **210 seconds** with modest speech tempo correction, rather than repeating a short script or adding minutes of silence. Invalid lengths fail clearly.
- Local Piper narration, original ambient score, footsteps, phone taps, pencil sounds, outdoor air and birds. No downloaded music.

This remains a procedural 2D rig, with a defined drawing library. It does not produce arbitrary fully animated scenes or guarantee the polish of a hand-directed film. The supported actions are idle, walk, sit, sleep, phone, write, exercise and reach. Scripts should stay within these settings/actions; new artwork requires code. Narration is voice-over, with no lip sync. The small CPU story model can still write awkward prose; review the editable script and video before publishing. The authored sample gives a reliable quality reference.

## Free execution and outputs

The standard public Ubuntu runner uses CPU inference and rendering. No persistent server or paid service is required. GitHub's applicable free usage and storage limits still apply; private repositories have plan allowances. Do not enable paid runners for this workflow.

The first native build takes several minutes. General AI stories download about 2.5 GB of model weights; the authored sample skips the language-model download. Both download a small speech model. Allow tens of minutes on a fresh runner. The job has a 90-minute timeout. Artifacts expire after seven days, so download films you want to keep.

Outputs: `film.mp4`, editable `story.json`, `storyboard.jpg`, `characters.png`, `captions.srt`, `narration.wav` and `report.json`. Repository sample video is compressed to 540p for size; workflow output is native 1080p.

## Run locally

Python 3.11/3.12, Linux x86-64 and FFmpeg:

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg fonts-dejavu-core build-essential cmake
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
CC=gcc CXX=g++ CMAKE_ARGS="-DGGML_NATIVE=OFF -DGGML_AVX2=ON -DGGML_FMA=ON -DGGML_F16C=ON -DLLAMA_CURL=OFF" CMAKE_BUILD_PARALLEL_LEVEL=2 python -m pip install -r requirements-ai.txt
python -m storyfilm.render --title "Depressed" --brief "Use the authored depression story. Male lead."
python -m storyfilm.verify output/film.mp4 --height 1080 --fps 12 --min-seconds 180 --max-seconds 240
```

Models are reused from `.cache`. The authored story does not require `requirements-ai.txt` for local rendering. `--character male` or `--character female` overrides selection.

To edit a generated screenplay, change the narration, locations, actions, expressions, `time` (`night/dawn/day`), `shot` (`wide/close`) or `prop_text` in `story.json`, then:

```bash
python -m storyfilm.render --title "Revised Film" --brief "My edited original story." --plan output/story.json --out revised
```

`target_seconds` must be 180–240 for production-length plans. The renderer fits narration to this duration with modest tempo correction. It rejects scripts that would require excessive acceleration or stretching. `prop_text` is optional text shown on a phone/notebook; `|` separates lines. The authors' sample includes actual notebook goals and the support message.

For a short offline debugging preview:

```bash
python -m storyfilm.render --title "A new day" --brief "She wakes up. She writes a goal. She walks outside. She decides to try again tomorrow." --planner template --voice none --preview --height 540 --fps 12
```

The explicit template path preserves brief sentences. It is a debugging tool, not the production writer, and is not required to last three minutes. `--preview` omits voice and shortens timings. `--voice espeak` is available with `espeak-ng`, with less natural speech. The default workflow uses Piper, never a silent fallback.

## Development

```bash
python -m unittest discover -s tests -v
```

Tests cover script length and continuity landmarks, lead selection, data-only inputs, native resolution, all rig actions, expression/movement differences, day/night backgrounds, object inserts, 12 FPS timing and captions. CI also renders and decodes a short MP4. Full acceptance renders and verifies the 3:30 sample at 1080p12. Workflow inputs pass through environment variables; commands use argument arrays. Repository permissions are read-only.

`planner.py`: screenplay and validation. `stories/depressed.json`: authored sample. `art.py`: original artwork and acting. `audio.py`: speech, timing and sound. `render.py`: orchestration and encoding. `verify.py`: dimensions, frame rate, duration, streams and complete decoding. See [THIRD_PARTY.md](THIRD_PARTY.md) for component licenses.
