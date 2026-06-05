FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# Before building, copy model.pt, mdv5a.pt, and labels.txt into this directory.
# Docker build contexts cannot reliably copy from parent directories.
COPY model.pt /app/model.pt
COPY mdv5a.pt /app/mdv5a.pt
COPY labels.txt /app/labels.txt

ENV PORT=8080
CMD ["gunicorn", "-b", ":8080", "app:app", "--timeout", "900", "--workers", "1"]
