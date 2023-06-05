import scrapy


class CityScraper(scrapy.Spider):
    name = "city-spider"

    def __init__(self, *args, **kwargs):
        with open("./data/state_urls.txt", "r") as statesfile:
            self.start_urls = [line.rstrip() for line in statesfile]

    def parse(self, response):
        city_urls = response.css('ul.centerwell-list.all-cities').css('a::attr(href)').getall()
        with open("./data/city_urls.txt", "a") as cityfile:
            for city_url in city_urls:
                cityfile.write(city_url)
                cityfile.write("\n")
