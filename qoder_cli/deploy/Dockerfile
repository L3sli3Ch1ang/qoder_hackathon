# SkillBridge SG — Docker image
# Dual purpose: (1) run locally via `docker run`, (2) deploy to free hosts
# (Hugging Face Spaces, Render, Koyeb).
#
# Build from the repository root so the image can copy app/, templates/, static/:
#   docker build -f deploy/Dockerfile -t skillbridge-sg .

# --- STAGE 1: Builder ---
FROM python:3.13-slim AS builder
WORKDIR /build

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc g++ \
    && rm -rf /var/lib/apt/lists/*

# Install CPU-only PyTorch
RUN pip install --no-cache-dir --user \
    torch --index-url https://download.pytorch.org/whl/cpu

# Install all requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# --- STAGE 2: Runtime ---
FROM python:3.13-slim
WORKDIR /home/appuser/app

# Minimal system tools
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user FIRST so --chown works on the next COPY
# (avoids a 1.3 GB duplicate layer from `chown -R` after the copy).
# Explicit chmod 755 so the appuser can create ~/.cache at model-pre-download time.
RUN useradd -m -u 1000 appuser \
    && chmod 755 /home/appuser

# Copy Python deps from builder, owned by appuser from the start
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

USER appuser

ENV HOME=/home/appuser \
    PATH=/home/appuser/.local/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/home/appuser/.cache/huggingface \
    HF_HUB_DISABLE_TELEMETRY=1 \
    SKILLBRIDGE_QDRANT_PATH=/home/appuser/qdrant_data \
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    PORT=7860

# Application code
COPY --chown=appuser:appuser app /home/appuser/app/app
COPY --chown=appuser:appuser templates /home/appuser/app/templates
COPY --chown=appuser:appuser static /home/appuser/app/static
COPY --chown=appuser:appuser deploy/start.sh /home/appuser/app/start.sh
RUN chmod +x /home/appuser/app/start.sh

# Models are downloaded on first request (not pre-downloaded to save build memory)
# HF_HOME is set to /home/appuser/.cache/huggingface for persistent storage

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -fsS http://127.0.0.1:${PORT}/health || exit 1

CMD ["./start.sh"]
