FROM python:3.11-slim

RUN apt-get update && apt-get install -y libpq-dev

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir -p /app/logs/

VOLUME /db_data /var/lib/postgresql/data

COPY . .

CMD ["scrapy", "crawl", "dvsvc"]
