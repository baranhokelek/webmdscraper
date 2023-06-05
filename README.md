# webmdscraper

Before running the scraper, create a virtual Python environment and make sure that `scrapy` module is installed.

Run the following commands:

```
scrapy crawl states-spider
```
```
scrapy crawl city-spider
```
```
scrapy crawl page-spider
```
```
scrapy crawl doctor-spider -O $filename.json -s LOG_FILE=path/to/log/file
```
