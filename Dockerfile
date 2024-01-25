FROM python:3.9

WORKDIR /app

RUN mkdir -p /app/mydb \
&& touch /app/mydb/test.db \
&& touch /app/mydb/log.log

VOLUME /app/mydb

COPY . /app

RUN pip3 install -r requirements.txt

RUN python3 installer.py

CMD ["python3", "./test_crawl/spiders/test.py"]