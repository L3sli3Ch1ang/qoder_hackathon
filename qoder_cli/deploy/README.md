# SkillBridge SG — Docker Deployment

This folder packages the app as a Docker image for **two purposes**:

1. **Run locally** on any Linux/macOS/Windows machine with Docker — users can pull and run it in one command.
2. **Deploy to a free, forever-free online host** so users can click a link and try
   the live app without installing anything.

The image is self-contained: Python deps, CPU-only PyTorch, seed data, templates, and
both ML models (`all-MiniLM-L6-v2` + `ms-marco-MiniLM-L-6-v2`) are **baked in at build
time**, so cold starts do not re-download models.

---

## 1. Build the image (from the repository root)

```bash
cd qoder_cli            # repo root (contains app/, templates/, static/)
docker build -f deploy/Dockerfile -t skillbridge-sg:latest .
```

Notes:
- Build context is the repo root so the image can copy `app/`, `templates/, `static/`.
  The root `.dockerignore` keeps the context small (excludes `.venv`, `.direnv`,
  `demo-video`, etc.).
- First build takes ~5–8 min (downloads CPU torch + the two HF models). Rebuilds reuse
  the layer cache and are much faster.
- Resulting image is ~1.2 GB (multi-stage build strips compiler tools).
- Runs as non-root user `appuser` (uid 1000) for security.
- Sets `OMP_NUM_THREADS=1` and `MKL_NUM_THREADS=1` to prevent PyTorch memory spikes.
- Default port is **7860**. Override with `PORT` env var.

---

## 2. Run locally

```bash
docker run -p 7860:7860 skillbridge-sg:latest
# Open http://127.0.0.1:7860 → paste a JD → ranked, explained results.
```

If port 7860 is taken, map a different host port (the container always listens on 7860
internally unless you set `PORT`):

```bash
docker run -p 8050:7860 skillbridge-sg:latest    # then open http://127.0.0.1:8050
```

To use a different container port:

```bash
docker run -p 8000:8000 -e PORT=8000 skillbridge-sg:latest
```

Verify:

```bash
curl http://127.0.0.1:7860/health        # → {"status":"ok"}
```

Optional — enable live LLM narratives (Alibaba Cloud DashScope). Without a key the app
still works fully and uses a grounded offline narrative template:

```bash
docker run -p 7860:7860 \
  -e SKILLBRIDGE_DASHSCOPE_API_KEY=sk-... \
  skillbridge-sg:latest
```

---

## 3. Free-forever online hosting — Render

**Render** is the recommended deployment target. Free tier, supports Docker, injects
`PORT` automatically (the app already honors it).

**Caveat**: Free instances sleep after ~15 min idle; first request after a sleep is a
cold start (~15–30 s).

### Steps to deploy:

1. Push this repo to GitHub (already done).
2. Go to https://dashboard.render.com → **New → Web Service**
3. Connect your GitHub repo (`L3sli3Ch1ang/qoder_hackathon`)
4. **Environment**: Docker
5. **Dockerfile Path**: `qoder_cli/deploy/Dockerfile`
6. **Plan**: Free
7. Click **Deploy**

You get a public URL like `https://skillbridge-sg.onrender.com`.

Render automatically injects the `PORT` environment variable, so no changes to the
Dockerfile are needed.

---

## 4. Files in this folder

| File | Purpose |
|---|---|
| `deploy/Dockerfile` | Multi-stage build: builder (torch+deps) → runtime (no compiler, non-root user) |
| `deploy/start.sh` | Entrypoint; runs uvicorn on `$PORT` (default 7860) |
| `.dockerignore` (repo root) | Keeps build context small |

## 5. Verified behaviour (tested)

- `GET /health` → `{"status":"ok"}` (container reports `healthy`)
- `POST /api/match` with an AI Governance JD → 10 ranked results, proficiency-aware
  scores, matched/gap/bridge skills, courses, narratives, and Emerging/CASL badges all
  populated correctly.
