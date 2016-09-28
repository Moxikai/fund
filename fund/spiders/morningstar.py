# -*- coding: utf-8 -*-
import scrapy


class MorningstarSpider(scrapy.Spider):
    name = "morningstar"
    allowed_domains = ["cn.morningstar.com"]
    start_urls = (
        'http://www.cn.morningstar.com/',
    )

    def parse(self, response):
        pass
