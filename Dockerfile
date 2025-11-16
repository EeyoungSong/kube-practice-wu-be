FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

# 캐시 최적화를 위해 requirements.txt를 먼저 복사
COPY requirements.txt .

# pip 업그레이드 및 의존성 설치 (병렬 설치로 속도 향상)
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --disable-pip-version-check -r requirements.txt

# Copy project files
COPY . .

# Create necessary directories and set permissions
RUN mkdir -p /app/staticfiles /app/media && \
    chown -R app:app /app

# Switch to non-root user
USER app

# Expose port
EXPOSE 8000

# Health check - 간단한 포트 체크
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD python -c "import socket; socket.create_connection(('localhost', 8000), timeout=5)" || exit 1

# Run collectstatic before gunicorn (migrate는 docker-compose에서 처리)
CMD ["sh", "-c", "python manage.py collectstatic --noinput && gunicorn --bind 0.0.0.0:8000 --workers 3 --timeout 120 config.wsgi:application"]
