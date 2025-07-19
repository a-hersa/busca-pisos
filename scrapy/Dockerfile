FROM python:3.11.7-slim-bullseye
RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN apt-get update && \
    apt-get install -y gcc libxml2-dev libxslt1-dev && \
    pip install --no-cache-dir -r requirements.txt
COPY . /code/
# Create necessary directories for scrapy operations
RUN mkdir -p /code/logs /code/inmobiliario/output /code/inmobiliario/crawls /code/inmobiliario/backend
# CMD ["scrapy", "crawl", "novedades"]
