import scrapy


class PageSpider(scrapy.Spider):
    name = "page-spider"

    def __init__(self, *args, **kwargs):
        with open("./data/city_urls.txt") as cityfile:
            self.start_urls = [line.rstrip() for line in cityfile]

    def parse(self, response, **kwargs):
        current_url = response.request.url
        num_pages = response.css('a.number::text')
        if num_pages is None or len(num_pages) == 0:
            last_page = 1
        else:
            last_page = int(num_pages[-1].get())
        with open("./data/page_urls.txt", "a") as pagefile:
            pagefile.write(current_url)
            pagefile.write("\n")
            for page_number in range(2, last_page+1):
                pagefile.write(current_url + f"?pagenumber={page_number}")
                pagefile.write("\n")
