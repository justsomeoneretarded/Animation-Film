# Storyfilm

Turn **a title and a story brief** into an original, narrated 2D short film with GitHub Actions. No API keys, paid inference service, GPU, or thumbnail generation.

[View the two original characters](examples/characters.png) · [View a storyboard](examples/storyboard.jpg) · [Download a 20-second narrated sample](examples/sample.mp4)

The included sample uses the explicit template planner and is compressed to 540p for repository size. The production workflow uses the AI planner and renders 1080p.

## Make your first film

1. Open this repository's **Actions** tab.
2. Select **Make a film**, then **Run workflow** on `main`.
3. Enter the **title** and **brief**, then run it.
4. When it finishes, open the run and download **film-N** under **Artifacts**. Unzip it and play `film.mp4`.

Example title: **One Small Step**

Example brief:
> A bald young woman feels stuck and spends her evenings scrolling in her bedroom. She puts her phone down and writes one tiny goal at her desk. The next morning she walks outside. She almost turns back, but sits in the park and notices how quiet her mind becomes. End on the rooftop at dawn: she has not fixed everything, but she chooses to try again tomorrow. Quiet, reflective, hopeful. Use the female lead.

Say **female lead / she** or **male lead / he** in the brief. One protagonist appears throughout a film. Both are bald adults, with subtle facial and silhouette differences. The optional glowing shadow symbolizes emotion; it is not a second human cast member.

A first run downloads approximately 3 GB of story-model weights plus dependencies and a small speech model. Expect minutes to tens of minutes; runner speed and film length determine runtime. The job stops after 90 minutes. There are no persistent servers. Artifacts expire after seven days: download films you want to keep. Public standard runners are generally free under GitHub's applicable terms; private repositories have plan allowances. Do not enable paid runners for this workflow.

## What is included

- Local Qwen2.5-1.5B-Instruct story planning with CPU int8 weights and validated structured narration: ordered events from the brief become eight scenes, and the model writes their narration.
- Two original procedural bald characters, male and female, selected once per film.
- Bedroom, desk, street, park, gym and rooftop settings.
- Idle, walk, sit, sleep, phone, write, exercise and reach poses, expressions and blinking.
- Slow camera pushes, atmospheric particles, emotional shadow, fades and letterboxing.
- Local Piper neural narration; an original generated ambient score and transition chimes.
- Phrase captions burned into the film plus an SRT file.
- 1920×1080, 24 fps, H.264/AAC MP4 with streaming-friendly metadata.
- Editable `story.json`, storyboard, character sheet, narration and generation report.

**Visual scope:** this is a stylized procedural animation engine, not a general AI video model. The artwork is intentionally simple and original. It does not reproduce the supplied films' exact designs or polish. Motion uses a reusable pose rig rather than hand-drawn frame-by-frame acting. The internal design canvas is 960×540, scaled to a 1080p output; increasing output resolution does not add drawn detail. No lip sync is included. Captions use estimated phrase timings. The scene planner anchors locations/actions to the brief’s ordered sentences, expanding short briefs to eight scenes. The story model is small and may write weak narration or return invalid JSON; Drawable scene fields come from the supported library. Validation requires exactly eight narration entries, and invalid model output gets one correction attempt. Optional `--strict-json` enforces the narration structure token by token, at a considerable CPU cost; the default validates after generation. If the correction still fails, the job fails clearly instead of silently pretending to be a generated story. Rerun or rewrite the brief if that happens.

For the most coherent results, describe a single protagonist, clear events, an obstacle and an ending. Keep physical actions within the included library. New settings/actions require adding artwork or rig code in `storyfilm/art.py`.

## Run locally

Python 3.11+, FFmpeg and DejaVu Sans are recommended. On Ubuntu:

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg fonts-dejavu-core
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install torch==2.6.0 --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements-ai.txt
python -m storyfilm.render --title "One Small Step" --brief "A woman puts down her phone, writes one goal, and walks outside. She struggles but chooses to try again."
python -m storyfilm.verify output/film.mp4
```

Model downloads happen on first use. Subsequent local runs reuse Hugging Face's cache and `.cache/voices`. No secrets are required.

### Render an edited story

Change the narration, locations, actions, emotions or shadow flags in a previous `story.json`, then:

```bash
python -m storyfilm.render --title "Revised Film" --brief "Revised version of my original story." --plan output/story.json --out revised
```

Use `--character male` or `--character female` to override the selected lead locally.

### Lightweight, offline story planning

```bash
python -m storyfilm.render --title "A new day" --brief "She wakes up. She writes a goal. She walks outside. She decides to try again tomorrow." --planner template
```

The template planner reuses the brief's sentences as narration and maps keywords to actions. It is useful for debugging and explicit sentence-by-sentence stories, **not equivalent to AI screenwriting**. Piper still needs a one-time voice download. For fully offline checks after installing basic dependencies, use `--planner template --voice none --preview --height 540 --fps 12`; this makes a short preview with score but no speech. `--voice espeak` is also supported if you install `espeak-ng`, with less natural speech. The production Actions workflow uses AI plus Piper and never silently falls back.

## Development

```bash
python -m unittest discover -s tests -v
```

`Check renderer` runs tests plus a small FFmpeg integration render on each push. `Full AI film acceptance` tests the complete default pipeline with a sample female-led brief when that acceptance workflow is changed, or when manually requested. `Make a film` runs only when manually requested. Title and brief enter through environment variables, never interpolated into shell commands; all external commands use argument arrays. Brief content is story data, not code. The workflow has read-only repository permissions.

Project layout: `planner.py` handles story generation and schema validation; `art.py` draws the assets; `audio.py` synthesizes speech and sound; `render.py` orchestrates and encodes; `verify.py` validates the finished media. See `THIRD_PARTY.md` for model/software licenses.
