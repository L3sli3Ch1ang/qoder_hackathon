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
- Build context is the repo root so the image can copy `app/`, `templates/`, `static/`.
  The root `.dockerignore` keeps the context small (excludes `.venv`, `.direnv`,
  `demo-video`, etc.).
- First build takes ~5–8 min (downloads CPU torch + the two HF models). Rebuilds reuse
  the layer cache and are much faster.
- Resulting image is ~1.2 GB (multi-stage build strips compiler tools).
- Runs as non-root user `appuser` (uid 1000) for security and HF Spaces compliance.
- Sets `OMP_NUM_THREADS=1` and `MKL_NUM_THREADS=1` to prevent PyTorch memory spikes
  that would exceed HF Spaces' 16 GB RAM limit.
- Default port is **7860** (Hugging Face Spaces standard). Override with `PORT` env var.

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

## 3. Publish the image to GitHub (so others can just run it)

Push to **GitHub Container Registry (ghcr.io)** — free, and tied to your repo. Anyone
with Docker can then run it without cloning or building:

```bash
# One-time: authenticate with a GitHub Personal Access Token (scope: write:packages)
docker login ghcr.io -u L3sli3Ch1ang -p $GITHUB_TOKEN
# If $GITHUB_TOKEN is not set, replace with your actual PAT:
# docker login ghcr.io -u L3sli3Ch1ang -p ghp_YOUR_TOKEN_HERE

# Tag and push
docker tag skillbridge-sg:latest ghcr.io/l3sli3chiang/qoder_hackathon-skillbridge:latest
docker push ghcr.io/l3sli3chiang/qoder_hackathon-skillbridge:latest
```

Then any user (Linux/macOS/Windows with Docker) runs:

```bash
docker pull ghcr.io/l3sli3chiang/qoder_hackathon-skillbridge:latest
docker run -p 7860:7860 ghcr.io/l3sli3chiang/qoder_hackathon-skillbridge:latest
```

Make the package public (otherwise pullers need auth):
`ghcr.io → your profile → Packages → qoder_hackathon-skillbridge → Package settings → Change visibility → Public`.

---

## 4. Free-forever online hosting (pick one)

All three options run this exact Docker image and have a genuinely free tier.

### Option A — Koyeb (recommended for this app)

Best for Docker deployments. Free forever, no credit card, auto-builds from GitHub.

1. Go to https://app.koyeb.com → **Create App**
2. **Deployment type**: Git (connect your GitHub repo `L3sli3Ch1ang/qoder_hackathon`)
3. **Builder**: Docker
4. **Dockerfile path**: `qoder_cli/deploy/Dockerfile`
5. **Port**: `7860` (or set `PORT=7860` in environment variables)
6. Click **Deploy**

Koyeb will auto-build from your repo on every push. You get a public URL like:
`https://skillbridge-sg.koyeb.app`

**Alternative**: Deploy from a pre-built Docker image (Docker Hub or GHCR):
1. **Create App** → **Docker image**
2. Image URL: `docker.io/YOUR_USERNAME/skillbridge-sg:latest` or `ghcr.io/l3sli3chiang/qoder_hackathon-skillbridge:latest`
3. **Port**: `7860`
4. Click **Deploy**

### Option B — Render (free tier)

Free web service, supports Docker, injects `PORT` automatically (the app already honors
it). Caveat: free instances sleep after ~15 min idle; first request after a sleep is a
cold start (~15–30 s).

1. Push this repo to GitHub (already done).
2. https://dashboard.render.com → **New → Web Service** → connect the repo.
3. **Environment: Docker** (Render finds `deploy/Dockerfile` — set
   `Dockerfile Path = qoder_cli/deploy/Dockerfile`).
4. Plan: **Free**. Deploy. You get `https://<name>.onrender.com`.

### Option C — Hugging Face Spaces

Best for ML demos. Free forever, no credit card, generous container hosting.

1. Go to https://huggingface.co/new-space
2. Space name: `skillbridge-sg`; **SDK: Docker**; **Dockerfile: Blank**.
3. In the new Space repo, replace the generated `Dockerfile` with the one here, or
   simply point it at your image. Simplest: create a `Dockerfile` in the Space that is:
   ```dockerfile
   FROM ghcr.io/l3sli3chiang/qoder_hackathon-skillbridge:latest
   ```
4. Add a `README.md` at the Space root with this YAML front matter so HF uses port 7860:
   ```yaml
   ---
   title: SkillBridge SG
   emoji: 🌉
   sdk: docker
   app_port: 7860
   ---
   ```
5. HF builds and serves it at `https://huggingface.co/spaces/<you>/skillbridge-sg`.

---

## 5. Files in this folder

| File | Purpose |
|---|---|
| `deploy/Dockerfile` | Multi-stage build: builder (torch+deps) → runtime (no compiler, non-root user) |
| `deploy/start.sh` | Entrypoint; runs uvicorn on `$PORT` (default 7860) |
| `.dockerignore` (repo root) | Keeps build context small |

## 6. Verified behaviour (tested)

- `GET /health` → `{"status":"ok"}` (container reports `healthy`)
- `POST /api/match` with an AI Governance JD → 10 ranked results, proficiency-aware
  scores, matched/gap/bridge skills, courses, narratives, and Emerging/CASL badges all
  populated correctly.
