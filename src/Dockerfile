# 1. Offizielles Python-Base-Image
FROM python:3.11-slim

# 2. 'uv' Binaries aus dem offiziellen Astral-Image kopieren
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 3. Environment-Variablen für Python & uv setzen
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# 4. Abhängigkeiten kopieren (für optimales Docker-Layer-Caching)
COPY pyproject.toml uv.lock* ./

# 5. Dependencies via uv installieren (ohne das eigene Projekt selbst zu bauen)
RUN uv sync --frozen --no-install-project --no-dev

# 6. Quellcode in das Image kopieren
COPY . .

# 7. Projekt final synchronisieren
RUN uv sync --frozen --no-dev

# 8. Standard-Befehl (kann von Ofelia überschrieben oder als job-exec aufgerufen werden)
CMD ["python", "main.py"]