FROM python:3.12-slim

# Prevent stdout/stderr buffering
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq \
    libicu \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd --create-home --shell /bin/bash app

WORKDIR /home/app

# Install Python dependencies
COPY apps/api/pyproject.toml apps/api/requirements*.txt ./
RUN pip install --no-cache-dir -r requirements*.txt

# Copy application code
COPY apps/api/app ./app

# Switch to app user
USER app

# Expose the app port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]