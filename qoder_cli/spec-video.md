# spec-video.md — SkillBridge Demo Video Production Spec

## Overview

**Format:** 2–3 minute MP4 demo video for hackathon submission
**Tool:** [HyperFrames](https://github.com/heygen-com/hyperframes) (open-source, Apache 2.0)
**Approach:** Write HTML/CSS/JS compositions → render deterministic MP4 via headless Chrome + FFmpeg

---

## 1. What is HyperFrames?

HyperFrames is an open-source framework by HeyGen for turning HTML, CSS, media, and
seekable animations into deterministic MP4 videos. It is **agent-native** — designed for
AI coding agents to author videos by writing plain HTML with data attributes for timing.

**Key properties:**
- HTML-native: compositions are HTML files with `data-*` timing attributes
- No build step: `index.html` plays as-is in the browser
- Deterministic: same input → same frames → same output
- Animation adapters: GreenSock Animation Platform (GSAP), CSS, Lottie, Three.js, Anime.js, Web Animations API (WAAPI)
- Command-Line Interface (CLI): `npx hyperframes init | preview | lint | render`

**Requirements:** Node.js 22+, FFmpeg 7+

---

## 2. Setup Procedure

### 2.1 Install prerequisites (NixOS)

```bash
# In flake.nix or shell.nix, add:
#   nodejs_22
#   ffmpeg_7

# Or temporarily:
nix-shell -p nodejs_22 ffmpeg_7
```

### 2.2 Install HyperFrames skills (for agent-assisted creation)

```bash
npx skills add heygen-com/hyperframes --full-depth
```

This installs the core skill set. The `/hyperframes` router skill handles all creation
workflows. For a product demo video, the relevant workflow is `/product-launch-video`.

### 2.3 Initialize the video project

```bash
cd /home/leslie/Documents/Qoder/2026-07-29/chat-2
npx hyperframes init demo-video
cd demo-video
```

This creates:
```
demo-video/
  index.html          ← the composition (your video as HTML)
  frame.md            ← design system for the video
  assets/             ← media files (screenshots, audio)
```

### 2.4 Production loop

```bash
npx hyperframes preview    # live-reload browser preview
npx hyperframes lint       # validate composition structure
npx hyperframes render     # render to MP4 (output.mp4)
```

---

## 3. Video Structure (3 min — final rendered)

### Scene breakdown (matches `demo-video/index.html`, rendered to `output.mp4`)

The composition was re-cut to front-load the two things judges most need to trust:
**how the matching engine actually works** (scene 4) and **where the data comes
from** (scene 12). The mission statement opens the film (scene 1) and the close
(scene 15) restates the purpose.

| Scene | Time | Duration | Content | Visual |
|---|---|---|---|---|
| 1. Title + Mission | 0:00 | 6s | "SkillBridge SG" + subtitle + **mission statement** | Fade-in title, dark bg, brand color |
| 2. Problem | 0:06 | 9s | Accountant with Data Analytics invisible to AI Governance roles | Animated text |
| 3. Solution | 0:15 | 8s | 8-stage hybrid pipeline + official SWDA data (2,030 roles, 12,007 skills) | Pipeline list |
| 4. **The Matching Engine** ★ | 0:23 | 24s | Deep dive: BM25 → dense → RRF (k=60) → cross-encoder → proficiency fit (PL 1–6) → hybrid score (0.3·sem + 0.7·fit, 40–98) → explainability → courses; funnel 150→50+50→30→10 | 8-row engine grid |
| 5. Live Demo — Input | 0:47 | 10s | Paste Account Operations Analyst JD | screenshot-input.png |
| 6. Live Demo — Results | 0:57 | 14s | Ranked results, hybrid scores 40–98 across 5 sectors, < 1 s | screenshot-results.png |
| 7. Explainability | 1:11 | 13s | Matched skills + PL annotations, gaps, bridges, courses | screenshot-card.png |
| 8. Upskill Perspective | 1:24 | 12s | Hire ↔ Upskill toggle reframes results, no re-query | screenshot-candidate.png |
| 9. What-if Skill Explorer | 1:36 | 13s | Skills start checked; uncheck or Clear all, pick your own; scores shift live (▲/▼) | screenshot-whatif.png |
| 10. Surprise Mode | 1:49 | 11s | Serendipity filter surfaces unexpected cross-sector matches | screenshot-surprise.png |
| 11. Full Toolkit | 2:00 | 10s | What-if, filters, "Why this match?", theme/framing | Feature list |
| 12. **Data Provenance** ★ | 2:10 | 18s | Not a black box: JDs ← real SWDA roles; candidates ← deterministic synthesis (seed 20260729, ~78% coverage, not AI-hallucinated); bridges ← K&A containment; courses ← MySkillsFuture | 4-row provenance grid |
| 13. Data Grounding Stats | 2:28 | 10s | 434 skills, 53 bridges, 150K+ K&A items, 5 sectors | Stats animation |
| 14. Qoder Usage | 2:38 | 10s | Quest Mode + Expert Mode + CLI, 2 weeks, 97 tests | Mode badges |
| 15. Close | 2:48 | 12s | "Skills don't retire at sector boundaries. Neither should people." + hashtags | Fade out |

### Total: 3 min 0 sec (180s @ 30fps = 5400 frames, 1920×1080, h264, ~10.1 MB)

---

## 4. Assets Needed

### 4.1 Screenshots captured (from the running app, dark theme, 1920×1080)

6 of the 7 captures in `demo-video/assets/` are referenced by the current
`index.html` (the landing/convergence shot is retained but no longer used — the
sector convergence strip is visible inside the What-if capture):

| # | File | What it shows |
|---|---|---|
| 1 | `screenshot-input.png` | JD input with Account Operations Analyst text pasted |
| 2 | `screenshot-results.png` | Ranked results (Hire perspective) with scores |
| 3 | `screenshot-card.png` | Single result card, "Why this match?" expanded (PL, gaps, bridges, courses) |
| 4 | `screenshot-candidate.png` | Upskill perspective ("Upskill potential" framing) |
| 5 | `screenshot-whatif.png` | What-if explorer with **all skills checked by default + Clear all**, results with ▲/▼ deltas + convergence strip |
| 6 | `screenshot-surprise.png` | Surprise mode ("Unexpected match" badge) |
| — | `screenshot-landing.png` | Landing page + convergence strip (unused in current cut, kept as spare) |

### 4.2 Audio (optional)

- Background music: lo-fi or corporate-tech (royalty-free)
- No voiceover required (text-driven video)

### 4.3 Brand assets

- SkillBridge logo (text-based is fine)
- Qoder logo (from qoder.ai)
- Alibaba Cloud logo (from alibabacloud.com)
- SWDA/SkillsFuture reference (text mention)

---

## 5. HyperFrames Composition (HTML structure)

The composition uses `data-start` (seconds) and `data-duration` (seconds) for timing,
`data-track-index` for layering, and GSAP for animations.

### Skeleton (index.html)

```html
<div id="stage" data-composition-id="skillbridge-demo"
     data-start="0" data-width="1920" data-height="1080">

  <!-- Scene 1: Title (0–5s) -->
  <div class="clip scene-title" data-start="0" data-duration="5" data-track-index="1">
    <h1>SkillBridge SG</h1>
    <p>Cross-Sector Skills Matching · Powered by SWDA Skills Framework</p>
  </div>

  <!-- Scene 2: Problem (5–20s) -->
  <div class="clip scene-problem" data-start="5" data-duration="15" data-track-index="1">
    <h2>The Problem</h2>
    <p>An accountant with "Data Analytics" is invisible to Infocomm Technology (ICT) roles.</p>
    <p>Existing platforms match by single-sector keywords only.</p>
  </div>

  <!-- Scene 3: Solution (20–30s) -->
  <div class="clip scene-solution" data-start="20" data-duration="10" data-track-index="1">
    <h2>The Solution</h2>
    <p>8-stage hybrid pipeline + official SWDA data (2,030 roles, 12K skills)</p>
  </div>

  <!-- Scene 4-7: Screenshots (30–105s) -->
  <img class="clip" data-start="30" data-duration="20" data-track-index="1"
       src="assets/screenshot-input.png" />
  <img class="clip" data-start="50" data-duration="30" data-track-index="1"
       src="assets/screenshot-results.png" />
  <img class="clip" data-start="80" data-duration="25" data-track-index="1"
       src="assets/screenshot-explainability.png" />

  <!-- Scene 8: Stats (105–120s) -->
  <div class="clip scene-stats" data-start="115" data-duration="15" data-track-index="1">
    <h2>Grounded in Real Data</h2>
    <div class="stat-grid">
      <span>434 skills</span><span>53 bridges</span><span>150K K&A items</span>
    </div>
  </div>

  <!-- Scene 9: Qoder (120–130s) -->
  <div class="clip scene-qoder" data-start="130" data-duration="10" data-track-index="1">
    <p>Built with Qoder Quest + Expert Mode</p>
  </div>

  <!-- Scene 10: Close (130–150s) -->
  <div class="clip scene-close" data-start="140" data-duration="10" data-track-index="1">
    <h2>SkillBridge SG</h2>
    <p>#QoderHackathon #BuildWithQoder</p>
  </div>

  <!-- Background music -->
  <audio data-start="0" data-duration="150" data-track-index="0"
         data-volume="0.3" src="assets/bgm.mp3"></audio>

  <!-- GSAP animations (pinned with a real Subresource Integrity (SRI) hash) -->
  <script src="https://cdn.jsdelivr.net/npm/gsap@3.12.7/dist/gsap.min.js"
          integrity="sha384-pEQB1h4Zmn9xhS6jotzltHSIQq6N0Oh3BXkCNOH5LKI81R2NRbb9efarAJYw9gTY"
          crossorigin="anonymous"></script>
  <script>
    const tl = gsap.timeline({ paused: true });
    tl.from(".scene-title h1", { opacity: 0, y: 40, duration: 0.8 }, 0.5);
    tl.from(".scene-title p", { opacity: 0, duration: 0.6 }, 1.2);
    tl.from(".scene-problem h2", { opacity: 0, x: -30, duration: 0.5 }, 5.5);
    // ... more animations per scene
    window.__timelines = window.__timelines || {};
    window.__timelines["skillbridge-demo"] = tl;
  </script>
</div>
```

---

## 6. Production Steps (for the user)

### Pre-production
1. [ ] Start the app: `uvicorn app.main:app --host 127.0.0.1 --port 8000`
2. [ ] Capture 5–6 screenshots (dark theme, various states)
3. [ ] Save screenshots to `demo-video/assets/`
4. [ ] (Optional) Download royalty-free BGM → `demo-video/assets/bgm.mp3`

### Production
5. [ ] Install HyperFrames: `npx hyperframes init demo-video`
6. [ ] Write/edit `demo-video/index.html` (use the skeleton above)
7. [ ] Style with CSS (dark theme, brand colors, clean typography)
8. [ ] Add GSAP animations (fade-ins, slides, scale)
9. [ ] Preview: `npx hyperframes preview`
10. [ ] Iterate until satisfied

### Post-production
11. [ ] Lint: `npx hyperframes lint`
12. [ ] Render: `npx hyperframes render` → produces `output.mp4`
13. [ ] Watch the MP4, check timing and quality
14. [ ] Upload to YouTube (unlisted) or direct link

### Submission
15. [ ] Include video URL in the hackathon submission form
16. [ ] Include video URL in the social post

---

## 7. Alternative: Agent-Assisted Creation

If using Qoder/Claude Code with HyperFrames skills installed:

```
Using /hyperframes, create a 2.5-minute product demo video for SkillBridge SG:
- Dark theme, clean typography, corporate-tech style
- Scenes: title → problem → solution → app screenshots → stats → Qoder usage → close
- Screenshots in assets/ folder
- Subtle GSAP fade-in animations
- Background music at 30% volume
- 1920x1080, 30fps
```

The agent will plan, write the HTML, wire animations, lint, preview, and render.

---

## 8. Design Guidelines

| Aspect | Choice |
|---|---|
| Resolution | 1920×1080 (16:9) |
| Frames Per Second (FPS) | 30 |
| Background | Dark (#0f172a slate-900) |
| Text | White/light gray |
| Accent | Teal/cyan (#06b6d4) for highlights |
| Typography | System sans-serif (Inter if available) |
| Transitions | Fade + subtle slide (0.5–0.8s) |
| Music | Lo-fi corporate, 30% volume, no lyrics |

---

## 9. HyperFrames CLI Reference

| Command | Purpose |
|---|---|
| `npx hyperframes init <name>` | Scaffold a new video project |
| `npx hyperframes preview` | Browser preview with live reload |
| `npx hyperframes lint` | Validate composition structure |
| `npx hyperframes render` | Render to MP4 |
| `npx hyperframes check` | Runtime diagnostics |
| `npx hyperframes snapshot` | Capture a single frame as PNG |
| `npx hyperframes doctor` | Verify environment (Node, FFmpeg) |
| `npx hyperframes add <block>` | Install a catalog block (transitions, overlays) |

---

## 10. Useful Catalog Blocks

```bash
npx hyperframes add flash-through-white   # scene transition
npx hyperframes add data-chart            # animated statistics
npx hyperframes add instagram-follow      # social Call-To-Action (CTA) overlay
```

Browse: https://hyperframes.heygen.com/catalog

---

*End of spec-video.md*
