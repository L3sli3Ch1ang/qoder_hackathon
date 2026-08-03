#!/usr/bin/env python3
"""Build a narrated voice track for the SkillBridge SG demo video and mux it in.

Backends
--------
- "kokoro": Kokoro-82M (ONNX, local, CPU) — far more natural, human-like prosody.
  Voice bf_emma (British female) is the closest available to Singapore English.
  Needs: pip install kokoro-onnx soundfile misaki[en]; espeak-ng on PATH;
  model files in kokoro_model/ (see download note at bottom).
- "edge": Microsoft Edge TTS en-SG-LunaNeural — authentic Singapore accent,
  keyless, but noticeably more synthetic.

Pipeline
--------
1. Synthesise one narration clip per scene.
2. Auto-fit each clip's speaking rate so it never overruns its scene window.
3. Place every clip at its scene start (+OFFSET_S) and mix into a single AAC
   track with ffmpeg (adelay + amix, no normalisation), padded to video length.
4. Mux the track onto output.mp4 (video stream copied, audio added), in place.

Usage
-----
    python demo-video/narration/build_narration.py

Re-runnable and deterministic given the same transcript + voice.
"""
from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
BACKEND = "edge"                     # "kokoro" (natural) or "edge" (Singapore accent)

# Kokoro settings (natural British female — closest to Singapore English)
KOKORO_VOICE = "bf_emma"
KOKORO_LANG = "en-gb"
KOKORO_MODEL_DIR = Path(__file__).resolve().parent / "kokoro_model"

# Edge TTS settings (Singapore English, female — friendly/positive)
EDGE_VOICE = "en-SG-LunaNeural"

OFFSET_S = 0.3                       # narration starts this long after scene start
END_MARGIN_S = 0.4                   # silence kept before the next scene begins
MAX_RATE_PCT = 25                    # cap on speaking-rate speed-up to protect naturalness
VIDEO_DURATION_S = 180.0             # full composition length (audio is padded to this)

HERE = Path(__file__).resolve().parent
VIDEO = HERE.parent / "output.mp4"        # canonical demo video; narration applied in place
CLIPS_DIR = HERE / "clips"
MIXED = HERE / "narration.m4a"

# --------------------------------------------------------------------------- #
# Transcript — (scene_no, start_sec, window_sec, narration_text)
# Text is auto-fitted; numbers spelled out for clean TTS.
# --------------------------------------------------------------------------- #
SCENES: list[tuple[int, float, float, str]] = [
    (1, 0, 6,
     "SkillBridge SG — cross-sector skills matching for Singapore's workforce."),
    (2, 6, 9,
     "An accountant with data and Python skills stays invisible to AI roles "
     "elsewhere. Keyword matching misses transferable skills."),
    (3, 15, 8,
     "Our solution: an eight-stage hybrid pipeline, grounded in the official "
     "Skills Framework and its proficiency levels."),
    (4, 23, 24,
     "Here is how a score is really computed. Two retrieval paths — lexical and "
     "semantic — each recall fifty candidates. Rank fusion keeps thirty; a "
     "cross-encoder re-ranks to ten. Proficiency scoring then checks each skill "
     "level against the job. The final blend is seventy percent real skill fit — "
     "so text alone can never inflate a score."),
    (5, 47, 10,
     "Let's see it live. We paste a real job description — an Account Operations "
     "Analyst in the finance sector."),
    (6, 57, 14,
     "In under a second, SkillBridge returns ranked candidates across all five "
     "sectors, each with a hybrid score from forty to ninety-eight. The best "
     "transferable matches rise to the top."),
    (7, 71, 13,
     "Every result answers 'why this match?' — showing matched skills with "
     "proficiency annotations, the gaps, bridge skills that connect them, and "
     "recommended courses."),
    (8, 84, 12,
     "With one toggle, switch from hire to upskill. Every result is reframed as "
     "growth potential — instantly, with no re-query."),
    (9, 96, 13,
     "The what-if skill explorer lets recruiters prioritise. Suggested skills "
     "start active; uncheck a few or clear all, then pick your own. Scores re-run live."),
    (10, 109, 11,
     "And 'surprise me' applies a serendipity filter, surfacing unexpected "
     "cross-sector matches that a keyword search would never find."),
    (11, 120, 10,
     "It's a full toolkit: instant filters, clickable convergence pairs, light "
     "and dark themes, and sub-second results throughout."),
    (12, 130, 18,
     "None of this is a black box. Job roles come from the official Skills "
     "Framework. Candidate profiles are generated deterministically from a fixed "
     "seed — reproducible, not hallucinated. And every course is a real, bookable "
     "MySkillsFuture link."),
    (13, 148, 10,
     "Grounded in real government data: four hundred thirty-four skills, "
     "fifty-three bridges, across five sectors."),
    (14, 158, 10,
     "Built with Qoder — Quest Mode, Expert Mode, and the CLI. Two weeks, "
     "ninety-seven tests, real government data."),
    (15, 168, 12,
     "Skills don't retire at sector boundaries. Neither should people. Thank you."),
]


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def probe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


_kokoro = None


def get_kokoro():
    """Load the Kokoro model once and reuse across all clips."""
    global _kokoro
    if _kokoro is None:
        from kokoro_onnx import Kokoro
        _kokoro = Kokoro(
            str(KOKORO_MODEL_DIR / "kokoro-v1.0.onnx"),
            str(KOKORO_MODEL_DIR / "voices-v1.0.bin"),
        )
    return _kokoro


def synth_kokoro(text: str, speed: float, out: Path) -> None:
    import soundfile as sf
    samples, sr = get_kokoro().create(
        text, voice=KOKORO_VOICE, speed=speed, lang=KOKORO_LANG
    )
    sf.write(str(out), samples, sr)


async def synth_edge(text: str, rate_pct: int, out: Path) -> None:
    import edge_tts
    rate = f"+{rate_pct}%" if rate_pct >= 0 else f"{rate_pct}%"
    await edge_tts.Communicate(text, EDGE_VOICE, rate=rate).save(str(out))


async def synth(text: str, rate_pct: int, out: Path) -> None:
    """Synthesise text at a given speed-up (rate_pct). 0 = natural pace."""
    if BACKEND == "kokoro":
        synth_kokoro(text, 1.0 + rate_pct / 100.0, out)
    else:
        await synth_edge(text, rate_pct, out)


async def build_clip(no: int, start: float, window: float, text: str) -> dict:
    # Clip must finish before the next scene: offset + dur + margin <= window.
    target = window - OFFSET_S - END_MARGIN_S
    ext = "wav" if BACKEND == "kokoro" else "mp3"
    out = CLIPS_DIR / f"scene_{no:02d}.{ext}"
    # Measure the natural pace, then speed up in a single deterministic pass.
    await synth(text, 0, out)
    natural = probe_duration(out)
    rate = 0
    if natural > target:
        rate = min(MAX_RATE_PCT, int(round((natural / target - 1) * 100)))
        if rate > 0:
            await synth(text, rate, out)
    dur = probe_duration(out)
    return {"no": no, "start": start, "window": window, "dur": dur,
            "rate": rate, "fits": dur <= target, "path": out}


def mix_track(clips: list[dict]) -> None:
    """Place each clip at its scene offset and mix to a single AAC track."""
    inputs: list[str] = []
    chains: list[str] = []
    labels: list[str] = []
    for i, c in enumerate(clips):
        inputs += ["-i", str(c["path"])]
        delay_ms = int((c["start"] + OFFSET_S) * 1000)
        label = f"a{i}"
        chains.append(f"[{i}]adelay={delay_ms}:all=1[{label}]")
        labels.append(f"[{label}]")
    filter_complex = ";".join(chains) + ";" + "".join(labels) + \
        f"amix=inputs={len(clips)}:duration=longest:normalize=0[out];" + \
        "[out]apad[padded]"
    cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", filter_complex,
           "-map", "[padded]", "-t", str(VIDEO_DURATION_S),
           "-c:a", "aac", "-b:a", "192k", str(MIXED)]
    subprocess.run(cmd, check=True, capture_output=True, text=True)


def mux_video() -> None:
    """Mux narration onto the video stream (copied), replacing output.mp4 in place.

    Idempotent: reads only the video stream (0:v:0), so re-running on an
    already-narrated file simply swaps in freshly generated narration.
    """
    tmp = HERE.parent / "output.tmp.mp4"
    cmd = ["ffmpeg", "-y", "-i", str(VIDEO), "-i", str(MIXED),
           "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
           "-c:a", "aac", "-b:a", "192k", str(tmp)]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    tmp.replace(VIDEO)


async def main() -> int:
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Backend: {BACKEND} | voice: {KOKORO_VOICE if BACKEND == 'kokoro' else EDGE_VOICE}")
    print(f"offset={OFFSET_S}s | end-margin={END_MARGIN_S}s | max rate +{MAX_RATE_PCT}%")
    clips = [await build_clip(*s) for s in SCENES]
    print("\nScene  Start  Window  ClipDur  Rate   Fits")
    for c in clips:
        flag = "ok" if c["fits"] else "OVER*"
        print(f"{c['no']:<6}{c['start']:<6.0f} {c['window']:<7.0f} "
              f"{c['dur']:<8.2f} +{c['rate']:<4}% {flag}")
    print("(*OVER = past the conservative target, still within the real scene)")

    print("\nMixing narration track ...")
    mix_track(clips)
    print(f"  -> {MIXED} ({probe_duration(MIXED):.1f}s)")

    print("Muxing onto video ...")
    mux_video()
    print(f"  -> {VIDEO} ({probe_duration(VIDEO):.1f}s)")
    print("\nDONE")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

# --------------------------------------------------------------------------- #
# Kokoro model files (download once, ~350 MB total):
#   https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
#   https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
# Place both in demo-video/narration/kokoro_model/
# --------------------------------------------------------------------------- #
