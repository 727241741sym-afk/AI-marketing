FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
  && apt-get install -y --no-install-recommends git build-essential \
  && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
ARG INSTALL_TRADINGAGENTS=false
RUN if [ "$INSTALL_TRADINGAGENTS" = "true" ]; then \
    pip install --no-cache-dir -e ".[tradingagents]"; \
  else \
    pip install --no-cache-dir -e .; \
  fi

COPY app ./app
COPY tests ./tests

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
