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

## 3. Free-forever online hosting — Render (Quick & Easy)

**Render** is the easiest deployment option. Free tier, supports Docker, injects
`PORT` automatically (the app already honors it).

**Caveat**: Free tier has 512MB RAM — may be tight for ML workloads. Free instances sleep after ~15 min idle; first request after a sleep is a cold start (~15–30 s).

### Steps to deploy:

1. Push this repo to GitHub (already done).
2. Go to https://dashboard.render.com → **New → Web Service**
3. Connect your GitHub repo (`L3sli3Ch1ang/qoder_hackathon`)
4. **Environment**: Docker
5. **Root Directory**: `qoder_cli` (important — this is the build context)
6. **Dockerfile Path**: `deploy/Dockerfile`
7. **Plan**: Free
8. Click **Deploy**

You get a public URL like `https://skillbridge-sg.onrender.com`.

Render automatically injects the `PORT` environment variable, so no changes to the
Dockerfile are needed.

---

## 4. Google Cloud Run (Auto-deploy from GitHub)

**Google Cloud Run** is a pay-per-use service with 2GB RAM. You only pay when requests come in — very cheap for demo traffic.

### Prerequisites:
- Google Cloud account: https://cloud.google.com/
- GitHub repo (already done)

### Step 1: Create Google Cloud Project

1. Go to https://console.cloud.google.com/
2. Click **Select a project** → **New Project**
3. **Project name**: `skillbridge-sg`
4. Click **Create**

### Step 2: Enable Required APIs

1. In your project, go to **APIs & Services** → **Library**
2. Search and enable:
   - **Cloud Run API**
   - **Cloud Build API**
   - **Artifact Registry API**

### Step 3: Create Artifact Registry (for Docker images)

1. Go to **Artifact Registry** → **Create repository**
2. **Name**: `skillbridge-repo`
3. **Format**: Docker
4. **Region**: `asia-southeast1` (Singapore) or closest to you
5. Click **Create**

### Step 4: Connect GitHub Repository

1. Go to **Cloud Run** → **Create service**
2. Click **Set up with Cloud Build** (or go to **Cloud Build** → **Triggers**)
3. Click **Connect repository**
4. Select **GitHub** → **Sign in with GitHub**
5. Authorize Google Cloud Build
6. Select repo: `L3sli3Ch1ang/qoder_hackathon`
7. Click **Connect**

### Step 5: Create Build Trigger

1. In **Cloud Build** → **Triggers** → **Create trigger**
2. **Name**: `skillbridge-deploy`
3. **Source**: GitHub → `L3sli3Ch1ang/qoder_hackathon`
4. **Branch**: `^main$`
5. **Included file filter**: `qoder_cli/**`
6. **Configuration**: Cloud Build configuration file
7. **Location**: `qoder_cli/cloudbuild.yaml`

### Step 6: Create cloudbuild.yaml

Create `qoder_cli/cloudbuild.yaml`:

```yaml
steps:
  # Build the Docker image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-f', 'deploy/Dockerfile', '-t', 'asia-southeast1-docker.pkg.dev/$PROJECT_ID/skillbridge-repo/skillbridge-sg:$SHORT_SHA', '.']
    dir: 'qoder_cli'

  # Push to Artifact Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'asia-southeast1-docker.pkg.dev/$PROJECT_ID/skillbridge-repo/skillbridge-sg:$SHORT_SHA']

  # Deploy to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'skillbridge-sg'
      - '--image=asia-southeast1-docker.pkg.dev/$PROJECT_ID/skillbridge-repo/skillbridge-sg:$SHORT_SHA'
      - '--region=asia-southeast1'
      - '--platform=managed'
      - '--allow-unauthenticated'
      - '--memory=2Gi'
      - '--cpu=1'
      - '--port=7860'
      - '--set-env-vars=PORT=7860'

images:
  - 'asia-southeast1-docker.pkg.dev/$PROJECT_ID/skillbridge-repo/skillbridge-sg:$SHORT_SHA'
```

### Step 7: Deploy Manually (First Time)

```bash
# Install Google Cloud CLI
curl https://sdk.cloud.google.com | bash

# Login
gcloud auth login

# Set project
gcloud config set project skillbridge-sg

# Configure Docker for Artifact Registry
gcloud auth configure-docker asia-southeast1-docker.pkg.dev

# Build and push
cd qoder_cli
docker build -f deploy/Dockerfile -t asia-southeast1-docker.pkg.dev/YOUR_PROJECT_ID/skillbridge-repo/skillbridge-sg:latest .
docker push asia-southeast1-docker.pkg.dev/YOUR_PROJECT_ID/skillbridge-repo/skillbridge-sg:latest

# Deploy
gcloud run deploy skillbridge-sg \
  --image=asia-southeast1-docker.pkg.dev/YOUR_PROJECT_ID/skillbridge-repo/skillbridge-sg:latest \
  --region=asia-southeast1 \
  --allow-unauthenticated \
  --memory=2Gi \
  --cpu=1 \
  --port=7860
```

### Step 8: Auto-deploy on Push

Now, every push to `main` that touches `qoder_cli/**` will automatically:
1. Build the Docker image
2. Push to Artifact Registry
3. Deploy to Cloud Run

You get a public URL like `https://skillbridge-sg-xxxxx.ap.run.app`.

---

## 5. Free-forever online hosting — Oracle Cloud Free Tier (24GB RAM)

**Oracle Cloud Free Tier** provides an always-free ARM instance with **24GB RAM** — perfect for ML workloads.

**Note**: ARM instances may show "Out of capacity" — try different availability domains (AD-2, AD-3) or wait for capacity.

### Prerequisites:
- Oracle Cloud account (free): https://www.oracle.com/cloud/free/
- SSH client
- GitHub repo pushed (already done)

### Step 1: Create Oracle Cloud Instance

1. Go to https://cloud.oracle.com/
2. Sign in or create account
3. Navigate to **Compute** → **Instances**
4. Click **Create instance**
5. Configure:
   - **Name**: `skillbridge-sg`
   - **Image**: Ubuntu 22.04 (or latest)
   - **Shape**: `VM.Standard.A1.Flex` (ARM, always free)
   - **OCPU count**: 1 (or up to 4 for free tier)
   - **Memory**: 6GB (or up to 24GB for free tier)
   - **SSH key**: Upload your public key
   - **Networking**: Public subnet + Assign public IP
6. Click **Create**

### Step 2: Connect to Instance

```bash
ssh ubuntu@<YOUR_INSTANCE_PUBLIC_IP>
```

### Step 3: Install Docker on Instance

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
sudo apt install -y docker.io

# Start Docker and enable on boot
sudo systemctl start docker
sudo systemctl enable docker

# Add ubuntu user to docker group (no sudo needed)
sudo usermod -aG docker $USER
newgrp docker

# Verify Docker works
docker --version
```

### Step 4: Clone Repo and Build

```bash
# Clone the repository
git clone https://github.com/L3sli3Ch1ang/qoder_hackathon.git
cd qoder_hackathon/qoder_cli

# Build the Docker image
docker build -f deploy/Dockerfile -t skillbridge-sg:latest .
```

### Step 5: Run the Container

```bash
# Run on port 80 (HTTP)
docker run -d \
  --name skillbridge \
  --restart unless-stopped \
  -p 80:7860 \
  skillbridge-sg:latest
```

### Step 6: Open Firewall Port

```bash
# Allow HTTP traffic
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -I OUTPUT -p tcp --sport 80 -j ACCEPT
```

Also in Oracle Cloud Console:
1. Go to **Networking** → **Virtual cloud networks** → your VCN
2. **Security Lists** → **Default Security List**
3. **Add Ingress Rule**:
   - Source: `0.0.0.0/0`
   - Protocol: TCP
   - Destination port: 80

### Step 7: Access Your App

Open browser: `http://<YOUR_INSTANCE_PUBLIC_IP>`

You get a permanent public URL like `http://123.45.67.89`

---

## 6. Files in this folder

| File | Purpose |
|---|---|
| `deploy/Dockerfile` | Multi-stage build: builder (torch+deps) → runtime (no compiler, non-root user) |
| `deploy/start.sh` | Entrypoint; runs uvicorn on `$PORT` (default 7860) |
| `deploy/cloudbuild.yaml` | Google Cloud Build config for auto-deploy |
| `.dockerignore` (repo root) | Keeps build context small |

## 7. Verified behaviour (tested)

- `GET /health` → `{"status":"ok"}` (container reports `healthy`)
- `POST /api/match` with an AI Governance JD → 10 ranked results, proficiency-aware
  scores, matched/gap/bridge skills, courses, narratives, and Emerging/CASL badges all
  populated correctly.
