FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# curl only — build-essential removed; --prefer-binary means no C compilation
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Phase 1: heavy data-science stack first, in isolation, using pre-built wheels only.
# Splitting this out prevents the single massive pip resolution that OOMs on Railway.
RUN pip install --no-cache-dir --prefer-binary --upgrade pip \
    && pip install --no-cache-dir --prefer-binary \
        "numpy>=2.2.6,<3.0.0" \
        "pandas>=2.2.0,<3.0.0" \
        "pandas-ta>=0.4.67b0,<0.5.0b0"

# Phase 2: remaining production dependencies (numpy/pandas already satisfied above).
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

COPY . .

# Railway injects PORT at runtime; default to 8001 for local Docker
ENV PORT=8001
EXPOSE ${PORT}

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 1 --log-level info"]
