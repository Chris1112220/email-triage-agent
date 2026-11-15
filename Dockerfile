# Build recipe for the Email Triage Agent API.
FROM python:3.12-slim

# Don't write .pyc files; print logs right away.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

# Install packages first so Docker can cache this step.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the app code (secrets are excluded by .dockerignore).
COPY app ./app

EXPOSE 8080

# Cloud Run sets PORT; default to 8080 locally.
CMD ["sh", "-c", "uvicorn app.api:app --host 0.0.0.0 --port ${PORT}"]