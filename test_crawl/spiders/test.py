from scrapy.linkextractors import LinkExtractor
import sqlite3
import scrapy
import warnings
import os
from rake_nltk import Rake
import nltk
from rake_nltk import Metric, Rake
import datetime
import logging
from fake_useragent import UserAgent

warnings.filterwarnings(
    "ignore", category=scrapy.exceptions.ScrapyDeprecationWarning)

db_path = "/app/mydb/test.db"


class Database:
    def __init__(self, db_path):
        self.db_path = db_path

    def insert(self, table_name, data):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO {} ({}) VALUES ({})"
                       .format(table_name, ",".join(data.keys()), ","
                               .join(["?"]*len(data))), list(data.values()))
        conn.commit()
        conn.close()

    def get_num_rows(self, table_name):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM {}".format(table_name))
        row = cursor.fetchone()
        conn.close()
        return row[0]

    def get_all_pages(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT url FROM all_pages")
        rows = cursor.fetchall()
        conn.close()
        return set([row[0] for row in rows])

    def get_first(self, table_name):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM {} LIMIT 1".format(table_name))
        row = cursor.fetchone()
        conn.close()
        return row

    def get_first_row_and_delete(self, table_name):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM {} LIMIT 1".format(table_name))
        row = cursor.fetchone()
        cursor.execute("DELETE FROM {} WHERE id={}".format(table_name, row[0]))
        conn.commit()
        conn.close()
        return row

    def get_last_row(self, table_name):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM {} ORDER BY id DESC LIMIT 1".format(table_name))
        row = cursor.fetchone()
        conn.close()
        return row

    def close(self):
        conn = sqlite3.connect(self.db_path)
        conn.close()

    def create_db_table(self):
        import os
        # delete if db exists
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
                CREATE TABLE IF NOT EXISTS all_pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL UNIQUE
            );''')
        conn.execute('''
                CREATE TABLE IF NOT EXISTS to_be_crawled (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL UNIQUE
            );''')
        conn.execute('''
                CREATE TABLE IF NOT EXISTS pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL UNIQUE
            );''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT,
                keyword TEXT
            );
        ''')
        conn.execute('''
                    CREATE TABLE IF NOT EXISTS statistics(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT,
                    new_url_found INTEGER,
                    total_new_url_found INTEGER,
                    crawled INTEGER,
                    to_be_crawled INTEGER,
                    total_keywords INTEGER,
                    download_latency REAL DEFAULT 0,
                    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    end_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    duration REAL DEFAULT 0
        );''')
        conn.commit()
        conn.close()


class Spider(scrapy.Spider):
    name = 'test_crawl'
    first_parse = True

    ua = UserAgent()
    fake_user_agent = ua.random

    custom_settings = {
        # 'LOG_LEVEL': logging.ERROR,
        # 'LOG_ENABLED': True,
        "USER_AGENT": fake_user_agent
    }

    def start_requests(self):
        """
        This method is called before crawling starts.

        It takes the first url from the to_be_crawled table and
        sends a request to it.

        It calls the parse method to process response.
        """
        db = Database(db_path)
        url = db.get_first_row_and_delete("to_be_crawled")[1]
        yield scrapy.Request(url=url, callback=self.parse,
                             headers={'User-Agent': self.settings['USER_AGENT']})

    def parse(self, response):
        """
        This method is called when a response is received.
        """
        db = Database(db_path)

        # extract all links from the response
        links = LinkExtractor(
            allow_domains=['appleinsider.com'],
            allow=[
                r'https:\/\/appleinsider.com.*',
                r'https:\/\/www.appleinsider.com.*'
            ],
            unique=True).extract_links(response)

        # get unique links
        links = set(link.url for link in links)
        links = links - db.get_all_pages()

        # insert links into database
        for link in links:
            db.insert("all_pages", {"url": link})
            db.insert("to_be_crawled", {"url": link})

        #####################
        # Extract keywords
        content_extract = self.extract_keywords(response)
        download_latency = response.meta.get('download_latency')

        # get keywords, and time to process them
        keywords = content_extract["keywords"]
        duration = content_extract["duration"]
        start_time = content_extract["start_time"]
        end_time = content_extract["end_time"]

        # insert keywords into database
        for keyword in keywords:
            db.insert("keywords", {"url": response.url, "keyword": keyword})

        # insert statistics into database
        try:
            db.insert("pages", {"url": response.url})
            db.insert("statistics", {
                "url": response.url,
                "new_url_found": len(links),
                "total_new_url_found": db.get_num_rows("all_pages"),
                "download_latency": download_latency,
                "start_time": start_time,
                "end_time": end_time,
                "duration": duration,
                "to_be_crawled": db.get_num_rows("to_be_crawled"),
                "total_keywords": db.get_num_rows("keywords"),
                "crawled": db.get_num_rows("pages"),
            })
        except sqlite3.IntegrityError:
            pass

        return

    def extract_keywords(self, response):
        """

        """

        # extract article text
        text = self.extract_article(response)
        extra_start_time = datetime.datetime.now()

        data = []

        if text == "":
            data = self.extract_meta_keywords(response)
        else:
            text = text.lower()
            r = Rake(
                min_length=1,
                max_length=3,
                language='english',
                include_repeated_phrases=False,
                ranking_metric=Metric.WORD_FREQUENCY,
            )
            r.extract_keywords_from_text(text)
            data = r.get_ranked_phrases()

        extra_end_time = datetime.datetime.now()

        return {
            "keywords": data,
            "duration": (extra_end_time - extra_start_time).total_seconds(),
            "start_time": extra_start_time,
            "end_time": extra_end_time,
        }

    def extract_meta_keywords(self, response):
        META_KEYWORDS_XPATH = r'//meta[@name="keywords"]/@content'
        keywords_str = response.xpath(META_KEYWORDS_XPATH).extract_first()
        return keywords_str.split(",") if keywords_str is not None else []

    def extract_article(self, response):
        ARTICLE_XPATH = r'//*[@id="top-half-snap"]/div/div[1]/article/div/div//p/text()'
        content = str(". ".join(response.xpath(
            ARTICLE_XPATH).getall())).strip()
        return content if content != "" else ""


if __name__ == '__main__':
    import subprocess

    db = Database(db_path)

    # comment out below lines if you want to resume the crawler
    db.create_db_table()
    db.insert("to_be_crawled", {"url": "https://www.appleinsider.com"})
    db.insert("all_pages", {"url": "https://www.appleinsider.com"})
    db.close()
    # cmment out above lines if you want to resume the crawler

    print("\033c", end="")

    try:
        while db.get_first("to_be_crawled"):
            subprocess.run(["scrapy", "crawl", "test_crawl",
                           "--logfile", "/app/mydb/log.log"])

            print("\033[H", end="")

            last_row = db.get_last_row("statistics")

            print("========================================")
            # show database path in the os
            print(f"Database path: {os.path.abspath(db_path)}")
            print(f"Size of database: {os.path.getsize(db_path) / 1000.0} KB")

            print("========================================")

            print(f"Number of URLs found: {last_row[3]}")
            print(f"Number of URLs crawled: {last_row[4]}")
            print(f"Number of URLs to be crawled: {last_row[5]}")
            print(f"Number of keywords extracted: {last_row[6]}")
            print("========================================")

    except KeyboardInterrupt:
        print("Process interrupted by user.")
    finally:
        print("Cleaning up...")
