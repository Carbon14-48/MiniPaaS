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

COPY src/scanners/rules/ /rules/

WORKDIR /app
COPY . .

EXPOSE 8000

CMD ["sh", "-c", "freshclam --daemon && uvicorn src.main:app --host 0.0.0.0 --port 8000"]
