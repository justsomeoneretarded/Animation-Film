# Third-party components

No frames, characters, audio, logos or backgrounds are extracted from the reference films. The character rig, environments, ambient composition and animation code are original to this project.

- **Qwen/Qwen2.5-1.5B-Instruct**: Apache-2.0, according to its Hugging Face model card: https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct . Model weights are downloaded at runtime, not committed.
- **Piper TTS** (`piper-tts` 1.4.2): GPL-3.0-or-later. https://github.com/OHF-voice/piper1-gpl . This project is delivered as source; Piper is installed separately by pip. Comply with its license when redistributing software that includes it.
- **en_US-ljspeech-medium** Piper voice: the exact voice model card is downloaded alongside the voice into `.cache/voices/MODEL_CARD`. Review it before distributing the model or using the voice commercially: https://huggingface.co/rhasspy/piper-voices/tree/main/en/en_US/ljspeech/medium . The LJSpeech dataset is public domain; this does not replace checking the model card.
- **FFmpeg**: LGPL/GPL depending on build options. Ubuntu's libx264-enabled build includes GPL components. https://ffmpeg.org/legal.html . FFmpeg is installed separately, not included in this repository.
- **DejaVu Sans**: DejaVu/Bitstream Vera font licenses. https://dejavu-fonts.github.io/License.html . Uses the system font; not bundled.
- **Pillow**, **NumPy**, **PyTorch**, **Transformers**, **Accelerate**, **Safetensors** and **ONNX Runtime** retain their upstream licenses.

Generated films do not include third-party model weights or software binaries. Review narration and story quality before publishing.
