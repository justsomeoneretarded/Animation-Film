# Storyfilm

Create an original **3–4 minute, 1920×1080, 12 FPS** animated film from a title and story brief in GitHub Actions. CPU only; no API keys, paid generation services or thumbnails.

## Make a film

1. Open **Actions → Make a film → Run workflow** on `main`.
2. Enter a title and a brief. Say **male lead / he**, or **female lead / she**.
3. Download the completed **film-N** artifact, unzip it, and play `film.mp4`.

Example for the general AI writer:

**Title:** `The Unfinished Page`

**Brief:**
> Female lead. She avoids answering a difficult message in her bedroom. She tries to write the truth in a notebook at her desk but stops. She takes a walk outside, then sits on a park bench. She returns to the message and sends a short honest answer instead of a perfect one. End at the same desk, writing again. Quiet and specific, with no instant transformation.

Give the character a desire, an obstacle, a concrete setback and a choice with a consequence. Four to eight chronological events work well. The generator must stage them within its supported locations and actions; arbitrary objects and activities need new artwork/code.

For the included, deliberately written example:

**Title:** `Depressed`

**Brief:** `Use the authored depression story. Male lead.`

That exact phrase (or `sample: depressed`) selects the included **30-shot, 3:30 example**. Change to `Female lead` to use the other protagonist. Other brief text does not rewrite this example; omit those phrases for the general writer.

## Shared v4 engine — applies to every new film

The reference study informed the shared renderer and general AI writer, not a title-specific visual patch.

- **Characters:** original rounded bodies and substantial curved limbs, short visible necks, small dark eyes, expressive brows/mouths. Bald male; female with hair. One selected human protagonist per film. A symbolic shadow can appear; supporting human characters are not implemented.
- **Acting:** planted idle poses, restrained breathing, emotional posture changes, walking with stance/swing phases, seated phone handling, typing/sending/receiving, notebook writing, reaching, knocking at the street door, a controlled barbell rep, falling and getting up. Actions have preparation, contact and recovery phases instead of unrelated arm waving.
- **Story:** the CPU Qwen3 4B writer first plans the complete arc, then writes the complete 36-shot arc in one pass, followed by sparse text direction. Each shot specifies a playable action, location, framing, emotion and actual object text. Scene descriptions are compiled from the animated actions; they cannot claim writing while the character is merely sitting. The text director adds only 4–6 story captions and at most four distinct shadow lines. The output schema permits supported action/location pairs and requires readable insert text. Remaining invalid data is retried. There is no 400-word narration quota.
- **Editing:** explicit wide, close, reaction and object-insert shots. No automatic halfway cut or perpetual zoom. Shot lengths are fitted proportionally to 210 seconds and quantized to 12 FPS.
- **Text:** brief white story captions, protagonist dialogue, red shadow lines, phone/notebook text and optional time/day labels are separate fields with separate timing. Receiving a message does not show a SENT label.
- **Environments:** sparse, clear bedroom, desk, street, park, gym and rooftop sets; night/day lighting, furniture contact, repeatable layouts and optional room clutter, rain and snow.
- **Shadow:** can loom, shrink or crack as part of a character choice. Its dialogue is optional.
- **Audio:** text-led by default, with an original ambient score and scene foley. Footsteps follow the walking cycle; writing, notification, send, knock and fall sounds follow action phases. Optional short `voiceover` lines use local Piper; no voice model is downloaded when there are no spoken lines.

This remains procedural 2D animation with a finite rig and set library. It does **not** guarantee the reference films' polish, arbitrary action choreography or excellent writing for every brief. It has no lip sync, generic supporting cast or full cinematic physics. Read the screenplay and review the film before publishing. Passing technical checks does not establish artistic similarity.

## Outputs

`film.mp4`, editable `story.json`, `screenplay.md`, `timeline.json`, `storyboard.jpg`, `characters.png`, `captions.srt`, `narration.wav` and `report.json`.

The Markdown screenplay and JSON timeline describe the exact staged shots. Story text can overlap intentionally in separate visual layers; the SRT is a convenience export. The MP4 contains the designed text layers. [Character designs](examples/characters.png) · [Read the example screenplay](examples/Depressed.md) · [Storyboard](examples/storyboard.jpg) · [Watch the verified sample](examples/sample.mp4). These examples use the shared v4 engine. The repository sample and workflow films are both 1920×1080 at 12 FPS.

## Free execution

Uses standard Ubuntu CPU runners. GitHub's applicable free compute, cache and artifact storage allowances apply, especially for private repositories. No persistent server is needed. General stories download about 2.5 GB of Apache-licensed writing-model weights and compile a CPU inference library. A fresh run can take tens of minutes; the timeout is 90 minutes. The authored example skips AI installation/download. Artifacts expire after seven days.

## Run locally

Python 3.11/3.12 on Linux x86-64 and FFmpeg:

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg fonts-dejavu-core build-essential cmake
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
CC=gcc CXX=g++ CMAKE_ARGS="-DGGML_NATIVE=OFF -DGGML_AVX2=ON -DGGML_FMA=ON -DGGML_F16C=ON -DLLAMA_CURL=OFF" CMAKE_BUILD_PARALLEL_LEVEL=2 python -m pip install -r requirements-ai.txt
python -m storyfilm.render --title "The Unfinished Page" --brief "Female lead. She avoids answering a difficult message. She writes at her desk, walks outside, then sends an honest answer. End with her writing again."
python -m storyfilm.verify output/film.mp4 --height 1080 --fps 12 --min-seconds 180 --max-seconds 240
```

The authored example does not need `requirements-ai.txt`. Models are cached in `.cache`. Outlines, complete action plans and text directions are checkpointed; GitHub Actions restores compatible story checkpoints when you retry the same title and brief. Changing either input starts a new story.

Edit `story.json` and render without replanning:

```bash
python -m storyfilm.render --title "Revised Film" --brief "My edited original story." --plan output/story.json --out revised
```

Keep `mode: text-led` and `version: 4`. Each shot needs `event`, `location`, `action`, `emotion`, and a 2–14 second `duration`; optional fields include `emotion_from`, `shot`, `time`, `state`, `weather` (`clear/rain/snow`), `caption`, `dialogue`, `prop_text`, `shadow`, `shadow_text`, `hud`, and `voiceover`. Production target is 180–240 seconds; use enough distinct material to fit naturally. The writer defaults to 210 seconds. Saved older narrated plans remain readable and use the new shared artwork.

For a shorter preview, add `--preview --height 540 --voice none`. The explicit `--planner template` path is a debug tool that preserves input sentences; it is not the production story writer.

## Development

```bash
python -m unittest discover -s tests -v
```

`visual_writer.py`: complete action story and sparse text direction. `screenplay.py`: shared contract and authored example. `staging.py`: shared characters, acting, sets and editing. `art.py`: drawing primitives and object inserts. `planner.py`: model loading, lead selection and legacy-plan support. `audio.py`: timing, speech and sound. `render.py`: exports and encoding. `verify.py`: full decode and media checks. See [THIRD_PARTY.md](THIRD_PARTY.md) for licenses.
