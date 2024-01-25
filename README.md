# Crawler

A simple crawler is running based on open-source Python library, namely Scrapy.

## Description

This Crawler only focuses on [appleinsider.com](https://appleinsider.com).

## Getting Started

### Dependencies

- Docker
- Sqlite3
- Python
  - Scrapy
  - Fake-Agent
  - rake_nltk

### Installing

1. Since this program is running in Docker, use this link [https://docker.com](https://docs.docker.com/get-docker/) to download Docker for your OS.

2. Go to directory `Crawler-in-Docker` in HW1 folder. You should see a list of folder and file, a file named `Dockerfile` is used to build docker image.
   3
   . On your Terminal or Commandline, run the following to build. Allow a few minutes to download dependencies and keyword extractor library.

```bash
docker build -t test_crawler:latest .
```

Where `test_crawler:latest` is image name and its tag.

4. Open Docker Dashboard to check if the build image is ready.

### Executing program

- On your Terminal or Commandline, run the following to run:

```bash
docker run -it test_crawler:latest
```

- The output should look like:

```bash
========================================
Database path: /app/mydb/test.db
Size of database: 1163.264 KB
========================================
Number of URLs found: 738
Number of URLs crawled: 43
Number of URLs to be crawled: 693
Number of keywords extracted: 9824
========================================
```

### Obtain the database

1. Open Docker Desktop, on tab Volumes, there is a created volume to store the database.

2. Right click on the `test.db`, press on Save As and pick the location where you would like to store the result database on your machine.

## Demo

## Discussions
