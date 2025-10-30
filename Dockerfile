FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps kept minimal; add gcc/libpq-dev only if you add Postgres or build-time deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Ensure entrypoint is executable (we'll invoke via sh to avoid shebang issues)
RUN chmod +x /app/entrypoint.prod.sh

EXPOSE 8000

# Use sh to run entrypoint for portability
CMD ["sh", "/app/entrypoint.prod.sh"]