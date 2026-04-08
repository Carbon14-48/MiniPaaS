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
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

RUN wget -qO- https://github.com/aquasecurity/trivy/releases/download/v0.56.0/trivy_0.56.0_Linux-64bit.tar.gz \
    | tar -xzf - -C /usr/local/bin trivy

RUN curl -fsSL https://github.com/sigstore/cosign/releases/latest/download/cosign-linux-amd64 -o /usr/local/bin/cosign \
    && chmod +x /usr/local/bin/cosign


FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    clamav \
    libclamav9 \
    clamav-freshclam \
    libclamunrar9 \
    && rm -rf /var/lib/apt/lists/* \
    && freshclam \
    && rm -rf /var/lib/clamav/*.cld /var/lib/clamav/*.cvd

COPY --from=builder /install /usr/local
COPY --from=builder /usr/local/bin/trivy /usr/local/bin/trivy
COPY --from=builder /usr/local/bin/cosign /usr/local/bin/cosign

COPY src/scanners/rules/ /rules/

WORKDIR /app
COPY . .

RUN mkdir -p /keys && chmod 755 /keys

EXPOSE 8000

CMD ["sh", "-c", "freshclam --daemon && uvicorn src.main:app --host 0.0.0.0 --port 8000"]
