FROM python:3.11.5-slim

WORKDIR /app

COPY requirements.txt .
# Install any dependencies your application needs
RUN pip install --no-cache-dir -r requirements.txt

# add app/ as py path var
ENV PYTHONPATH=/app:$PYTHONPATH
