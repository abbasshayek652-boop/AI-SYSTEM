# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

# The platform supplies PORT. mother_ai.run uses PORT (default 8000),
# so this image has exactly one server entrypoint and does not hard-code
# a second Uvicorn process.
EXPOSE 8000

CMD ["python", "-m", "mother_ai.run"]
