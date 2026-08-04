# SkillBridge SG — Docker image
# Dual purpose: (1) run locally via `docker run`, (2) deploy to free hosts
# (Hugging Face Spaces, Render, Koyeb).
#
# Build from the repository root so the image can copy app/, templates/, static/:
#   docker build -f deploy/Dockerfile -t skillbridge-sg .

FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/models \
    HF_HUB_DISABLE_TELEMETRY=1 \
    SKILLBRIDGE_QDRANT_PATH=/srv/qdrant_data

WORKDIR /srv

# Minimal system tooling. curl is used for the container HEALTHCHECK.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# CPU-only PyTorch first (much smaller than the CUDA build; the app is CPU-only).
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Application code + assets.
COPY app /srv/app
COPY templates /srv/templates
COPY static /srv/static

# Bake the two HF models into the image so cold starts do not re-download them.
RUN python - <<'PY'
from sentence_transformers import SentenceTransformer, CrossEncoder
SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
print("models cached OK")
PY

COPY deploy/start.sh /srv/start.sh
RUN chmod +x /srv/start.sh

# Default port; hosts that inject PORT (Render) or need 7860 (HF) override this.
ENV PORT=8000
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -fsS http://127.0.0.1:${PORT}/health || exit 1

CMD ["/srv/start.sh"]
