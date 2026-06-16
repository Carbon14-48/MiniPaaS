FROM python:3.12.13-slim AS builder
RUN rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --only-binary :all: --prefix=/install -r requirements.txt

FROM python:3.12.13-slim
RUN rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /install /usr/local
COPY . .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import socket;s=socket.socket();s.connect(('localhost',8000));s.close()" || exit 1

USER nobody

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
