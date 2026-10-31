FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --system --uid 10001 appuser

COPY src/ ./src/

USER 10001

EXPOSE 5000

CMD ["python", "src/app.py"]
