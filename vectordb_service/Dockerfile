FROM python:3.11.5-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# since you have some additional utils extend python path variable
ENV PYTHONPATH=/app:$PYTHONPATH
