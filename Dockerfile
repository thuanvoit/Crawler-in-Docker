# syntax=docker/dockerfile:1

# FROM ubuntu:22.04

FROM python:3.9

WORKDIR /app

RUN mkdir -p /app/mydb \
&& touch /app/mydb/test.db \
&& touch /app/mydb/log.log

VOLUME /app/mydb

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . /app

CMD ["python3", "/app/test_crawl/spiders/test.py"]