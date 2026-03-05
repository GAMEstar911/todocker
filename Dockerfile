FROM python:3.12

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install base requirements first (cached layer)
COPY base-requirements.txt .
RUN pip install --default-timeout=100 --retries 5 --no-cache-dir --verbose -r base-requirements.txt

# Install the rest of the requirements
COPY requirements.txt .
RUN pip install --default-timeout=100 --retries 5 --no-cache-dir --verbose -r requirements.txt

# Copy the rest of the application code
COPY . .

RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app

USER appuser
EXPOSE 8080

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 2 --threads 4 --worker-class gthread --timeout 120 app:app"]