import scrapy
import os


class StatesSpider(scrapy.Spider):
    name = "states-spider"

    def __init__(self, *args, **kwargs):
        self.start_urls = ["https://doctor.webmd.com/providers"]

    def parse(self, response):
        state_urls = response.css('a.state-name::attr(href)').getall()
        if not os.path.exists('./data'):
            os.makedirs('./data')
        with open("./data/state_urls.txt", "a+") as statesfile:
            for state_url in state_urls:
                statesfile.write(state_url)
                statesfile.write("\n")
