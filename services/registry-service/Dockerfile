FROM python:3.11-slim
WORKDIR /app
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends curl docker.io && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir --only-binary :all: --timeout 120 --retries 5 -r requirements.txt
COPY . .
EXPOSE 8005

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import socket;s=socket.socket();s.connect(('localhost',8005));s.close()" || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8005"]
