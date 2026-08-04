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
- Resulting image is ~1.65 GB.

---

## 2. Run locally

```bash
docker run -p 8000:8000 skillbridge-sg:latest
# Open http://127.0.0.1:8000 → paste a JD → ranked, explained results.
```

If port 8000 is taken, map a different host port (the container always listens on 8000
internally unless you set `PORT`):

```bash
docker run -p 8050:8000 skillbridge-sg:latest    # then open http://127.0.0.1:8050
```

Verify:

```bash
curl http://127.0.0.1:8000/health        # → {"status":"ok"}
```

Optional — enable live LLM narratives (Alibaba Cloud DashScope). Without a key the app
still works fully and uses a grounded offline narrative template:

```bash
docker run -p 8000:8000 \
  -e SKILLBRIDGE_DASHSCOPE_API_KEY=sk-... \
  skillbridge-sg:latest
```

---

## 3. Publish the image to GitHub (so others can just run it)

Push to **GitHub Container Registry (ghcr.io)** — free, and tied to your repo. Anyone
with Docker can then run it without cloning or building:

```bash
# One-time: authenticate with a GitHub Personal Access Token (scope: write:packages)
echo $GITHUB_TOKEN | docker login ghcr.io -u L3sli3Ch1ang --password-stdin

# Tag and push
docker tag skillbridge-sg:latest ghcr.io/l3sli3chiang/qoder_hackathon-skillbridge:latest
docker push ghcr.io/l3sli3chiang/qoder_hackathon-skillbridge:latest
```

Then any user (Linux/macOS/Windows with Docker) runs:

```bash
docker pull ghcr.io/l3sli3chiang/qoder_hackathon-skillbridge:latest
docker run -p 8000:8000 ghcr.io/l3sli3chiang/qoder_hackathon-skillbridge:latest
```

Make the package public (otherwise pullers need auth):
`ghcr.io → your profile → Packages → qoder_hackathon-skillbridge → Package settings → Change visibility → Public`.

---

## 4. Free-forever online hosting (pick one)

All three options run this exact Docker image and have a genuinely free tier.

### Option A — Hugging Face Spaces (recommended for this app)

Best for ML demos. Free forever, no credit card, generous container hosting.

1. Go to https://huggingface.co/new-space
2. Space name: `skillbridge-sg`; **SDK: Docker**; **Dockerfile: Blank**.
3. In the new Space repo, replace the generated `Dockerfile` with the one here, or
   simply point it at your image. Simplest: create a `Dockerfile` in the Space that is:
   ```dockerfile
   FROM ghcr.io/l3sli3chiang/qoder_hackathon-skillbridge:latest
   ```
4. Add a `README.md` at the Space root with this YAML front matter so HF uses port 8000:
   ```yaml
   ---
   title: SkillBridge SG
   emoji: 🌉
   sdk: docker
   app_port: 8000
   ---
   ```
5. HF builds and serves it at `https://huggingface.co/spaces/<you>/skillbridge-sg`.

### Option B — Render (free tier)

Free web service, supports Docker, injects `PORT` automatically (the app already honors
it). Caveat: free instances sleep after ~15 min idle; first request after a sleep is a
cold start (~15–30 s).

1. Push this repo to GitHub (already done).
2. https://dashboard.render.com → **New → Web Service** → connect the repo.
3. **Environment: Docker** (Render finds `deploy/Dockerfile` — set
   `Dockerfile Path = deploy/Dockerfile`).
4. Plan: **Free**. Deploy. You get `https://<name>.onrender.com`.

### Option C — Koyeb (free tier)

Free Docker hosting with a public URL.

1. https://app.koyeb.com → **Create App** → choose repo or a Docker image.
2. If using the image: `ghcr.io/l3sli3chiang/qoder_hackathon-skillbridge:latest`.
3. Set the port to `8000`. Deploy on the free tier.

---

## 5. Files in this folder

| File | Purpose |
|---|---|
| `deploy/Dockerfile` | Multi-step build: CPU torch → deps → app → bake ML models → start |
| `deploy/start.sh` | Entrypoint; runs uvicorn on `$PORT` (default 8000) |
| `.dockerignore` (repo root) | Keeps build context small |

## 6. Verified behaviour (tested)

- `GET /health` → `{"status":"ok"}` (container reports `healthy`)
- `POST /api/match` with an AI Governance JD → 10 ranked results, proficiency-aware
  scores, matched/gap/bridge skills, courses, narratives, and Emerging/CASL badges all
  populated correctly.
