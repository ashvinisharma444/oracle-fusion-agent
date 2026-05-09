FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for Playwright Chromium
RUN apt-get update && apt-get install -y \
    wget curl gnupg ca-certificates \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 \
    libxrandr2 libgbm1 libasound2 libpango-1.0-0 libcairo2 \
    libdbus-1-3 libexpat1 libfontconfig1 libglib2.0-0 \
    libx11-6 libxcb1 libxext6 fonts-liberation fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (without --with-deps since we install deps above)
RUN playwright install chromium

# Copy application
COPY app/ ./app/

# Create required directories
RUN mkdir -p /tmp/screenshots /tmp/traces

# Non-root user
RUN useradd -m -u 1000 agent && chown -R agent:agent /app /tmp/screenshots /tmp/traces
USER agent

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/api/v1/health || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2"]
