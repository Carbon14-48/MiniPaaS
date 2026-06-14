FROM python:3.12-slim AS builder

WORKDIR /app

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
RUN pip install --no-cache-dir --timeout 120 --retries 5 yara-python


FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    clamav \
    clamav-daemon \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Trivy
RUN curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- latest
RUN mv bin/trivy /usr/local/bin/ && chmod +x /usr/local/bin/trivy

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Download and install YARA rules
RUN mkdir -p /rules
COPY src/scanners/rules/ /rules/

# Initialize ClamAV database
RUN freshclam || true

# Configure and start ClamAV daemon
RUN mkdir -p /var/run/clamav /var/lib/clamav /var/log/clamav && \
    chown -R clamav:clamav /var/run/clamav /var/lib/clamav /var/log/clamav && \
    echo "clamav:clamav" | chpasswd || true

RUN printf '%s\n' "LogFile /var/log/clamav/clamd.log" "LogFileMaxSize 10M" "LogTime yes" "PidFile /var/run/clamav/clamd.pid" "TemporaryDirectory /tmp" "DatabaseDirectory /var/lib/clamav" "LocalSocketGroup clamav" "LocalSocketMode 660" "LocalSocket /var/run/clamav/clamd.ctl" "FixStaleSocket yes" "TCPSocket 3310" > /etc/clamav/clamd.conf

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout 120 --retries 5 -r requirements.txt

COPY . .

EXPOSE 8000

RUN printf '#!/bin/bash\nset -e\nnohup /usr/sbin/clamd --config-file=/etc/clamav/clamd.conf > /var/log/clamav/clamd.log 2>&1 &\nsleep 5\nuvicorn src.main:app --host 0.0.0.0 --port 8000\n' > /start.sh && chmod +x /start.sh

CMD ["/start.sh"]