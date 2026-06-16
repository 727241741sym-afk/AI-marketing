FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
  && apt-get install -y --no-install-recommends git build-essential \
  && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY app ./app
ARG INSTALL_TRADINGAGENTS=true
RUN python -m venv /opt/venv \
  && /opt/venv/bin/pip install --upgrade pip \
  && if [ "$INSTALL_TRADINGAGENTS" = "true" ]; then \
    /opt/venv/bin/pip install --no-cache-dir -e ".[tradingagents]"; \
  else \
    /opt/venv/bin/pip install --no-cache-dir -e .; \
  fi

FROM python:3.12-slim

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app
RUN adduser --disabled-password --gecos "" atlas
COPY --from=builder /opt/venv /opt/venv
COPY app ./app

EXPOSE 8000

USER atlas
CMD ["sh", "-c", "if [ \"$SERVICE_ROLE\" = \"worker\" ]; then python -m app.worker; else uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}; fi"]
