import scrapy
import os


class StatesSpider(scrapy.Spider):
    name = "states-spider"

    def __init__(self, *args, **kwargs):
        self.start_urls = ["https://doctor.webmd.com/providers"]

    def parse(self, response):
        print("Current Directory:", os.getcwd())
        state_urls = response.css('a.state-name::attr(href)').getall()
        with open("./data/state_urls.txt", "a+") as statesfile:
            for state_url in state_urls:
                statesfile.write(state_url)
                statesfile.write("\n")
