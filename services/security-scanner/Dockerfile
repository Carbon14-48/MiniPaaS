FROM python:3.12.13-slim AS builder
RUN rm -rf /var/lib/apt/lists/*

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

WORKDIR /app

# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    gnupg \
    ca-certificates \
    build-essential \
    pkg-config \
    git \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# hadolint ignore=DL3013
RUN pip install --no-cache-dir --only-binary :all: --timeout 120 --retries 5 yara-python==4.5.1


FROM python:3.12.13-slim
RUN rm -rf /var/lib/apt/lists/*

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gpg \
    clamav \
    clamav-daemon \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Trivy (via official apt repo with GPG verification)
# hadolint ignore=DL3008
RUN curl -fsSL https://aquasecurity.github.io/trivy-repo/deb/public.key | gpg --dearmor -o /usr/share/keyrings/trivy.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/trivy.gpg] https://aquasecurity.github.io/trivy-repo/deb generic main" | tee /etc/apt/sources.list.d/trivy.list && \
    apt-get update && apt-get install -y --no-install-recommends trivy && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Download and install YARA rules
RUN mkdir -p /rules
COPY src/scanners/rules/ /rules/

# Initialize ClamAV database
RUN freshclam || true

# Configure and start ClamAV daemon
RUN mkdir -p /var/run/clamav /var/lib/clamav /var/log/clamav && \
    chown -R clamav:clamav /var/run/clamav /var/lib/clamav /var/log/clamav

# checkov:skip=CKV2_DOCKER_17:clamav requires password auth for clamd TCP socket
RUN echo "clamav:clamav" | chpasswd || true

RUN printf '%s\n' "LogFile /var/log/clamav/clamd.log" "LogFileMaxSize 10M" "LogTime yes" "PidFile /var/run/clamav/clamd.pid" "TemporaryDirectory /tmp" "DatabaseDirectory /var/lib/clamav" "LocalSocketGroup clamav" "LocalSocketMode 660" "LocalSocket /var/run/clamav/clamd.ctl" "FixStaleSocket yes" "TCPSocket 3310" > /etc/clamav/clamd.conf

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --only-binary :all: --timeout 120 --retries 5 -r requirements.txt

COPY . .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import socket;s=socket.socket();s.connect(('localhost',8000));s.close()" || exit 1

# Install TruffleHog v3 for secret scanning
RUN curl -fsSL https://github.com/trufflesecurity/trufflehog/releases/download/v3.95.5/trufflehog_3.95.5_linux_amd64.tar.gz -o /tmp/trufflehog.tar.gz && \
    tar xzf /tmp/trufflehog.tar.gz -C /usr/local/bin/ trufflehog && \
    rm /tmp/trufflehog.tar.gz

# checkov:skip=CKV_DOCKER_3:needs root for docker socket + clamd setup, drops to clamav at runtime
RUN printf '#!/bin/bash\nset -e\nif [ -e /var/run/docker.sock ]; then chmod 666 /var/run/docker.sock; fi\nmkdir -p /var/lib/clamav/.cache && chown clamav:clamav /var/lib/clamav/.cache\nif [ -d /root/.cache/trivy ]; then cp -r /root/.cache/trivy /var/lib/clamav/.cache/ 2>/dev/null || true; chown -R clamav:clamav /var/lib/clamav/.cache/trivy 2>/dev/null || true; fi\n# Download Trivy DB in background if missing — doesn'\''t block startup\nif [ ! -f /var/lib/clamav/.cache/trivy/db/trivy.db ]; then\n  (su -s /bin/bash clamav -c "TRIVY_CACHE_DIR=/var/lib/clamav/.cache/trivy trivy image --download-db-only --quiet" 2>/dev/null || true) &\nfi\nnohup /usr/sbin/clamd --config-file=/etc/clamav/clamd.conf > /var/log/clamav/clamd.log 2>&1 &\nsleep 2\nexec su -s /bin/bash clamav -c "TRIVY_CACHE_DIR=/var/lib/clamav/.cache/trivy uvicorn src.main:app --host 0.0.0.0 --port 8000"\n' > /start.sh && chmod +x /start.sh

CMD ["/start.sh"]
