# syntax=docker/dockerfile:1

# FROM ubuntu:22.04

FROM python:3.9

RUN mkdir -p /mydb \
&& touch /mydb/test.db

VOLUME /mydb

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY installer.py installer.py
RUN python3 installer.py

COPY . .

CMD ["python3", "./test_crawl/spiders/test.py"]