FROM python:3.12-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create config directory for SQLite
RUN mkdir -p /app/config

# Expose dashboard port
EXPOSE 5075

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5075/')" || exit 1

CMD ["python", "app.py"]
