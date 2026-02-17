FROM python:3.13-slim

WORKDIR /app

# Install system dependencies for mysqlclient
RUN apt-get update -o Acquire::ForceIPv4=true \
    && apt-get install -y --no-install-recommends \
       gcc \
       pkg-config \
       default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*


COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app.py"]
