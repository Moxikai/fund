# -*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import scrapy
from scrapy import FormRequest
import re
class MorningstarSpider(scrapy.Spider):
    name = "morningstar"
    allowed_domains = ["cn.morningstar.com"]
    start_urls = (
        'http://cn.morningstar.com/quickrank/default.aspx',
    )

    def parse(self, response):
        """解析基金明细数据"""
        tr_list = response.xpath('//tr[contains(@class,"Item")]')
        try:
            result = [{'id':tr.xpath('td[@class="msDataText"][1]/a/text()').extract_first(),
                    'link':tr.xpath('td[@class="msDataText"][2]/a/@href').extract_first(),
                    'name':tr.xpath('td[@class="msDataText"][2]/a/text()').extract_first(),
                    'type':tr.xpath('td[@class="msDataText"][3]/text()').extract_first(),
                    'remark3':tr.xpath('td[@class="msDataText"][4]/img/@src').extract_first(),
                    'remark5':tr.xpath('td[@class="msDataText"][5]/img/@src').extract_first(),
                    'netValueDate':tr.xpath('td[@class="msDataNumeric"][1]/text()').extract_first(),
                    'unitNet':tr.xpath('td[@class="msDataNumeric"][2]/text()').extract_first(),
                    'DailyVariationOfNet':tr.xpath('td[@class="msDataNumeric"][3]/text()').extract_first(),
                    'rateOfReturn':tr.xpath('td[@class="msDataNumeric"][4]/text()').extract_first(),
                    } for tr in tr_list]
            for item in result:
                yield item

        except Exception as e:
            print '解析基金列表页------%s-------出错!'%(response.url)
        """获取总页码"""
        a = response.xpath('//a[contains(text(),">>")]/@href').extract()[-1]
        print a
        pattern = re.compile("'(\d{1,})'")
        total = pattern.findall(a)
        if total:
            print total
            formdata = {}
            for page in range(2,int(total[0])+1):
                """获取下一页post数据"""
                formdata['__EVENTTARGET'] = 'ctl00$cphMain$AspNetPager1'
                formdata['__EVENTARGUMENT'] = str(page)
                formdata['__VIEWSTATE'] = response.xpath('//input[@type="hidden" and @name="__VIEWSTATE"]/@value').extract_first()
                formdata['__EVENTVALIDATION'] = response.xpath('//input[@type="hidden" and @name="__EVENTVALIDATION"]/@value').extract_first()
                formdata['__LASTFOCUS'] = ''
                formdata['ctl00$cphMain$ddlCompany'] = ''
                formdata['ctl00$cphMain$ddlPortfolio'] = ''
                formdata['ctl00$cphMain$ddlWatchList'] = ''
                formdata['ctl00$cphMain$txtFund'] = u'基金名称'
                formdata['ctl00$cphMain$ddlPageSite'] = '25'

                yield FormRequest(url=self.start_urls[0], formdata=formdata, callback=self.parse)
                """
            for key in formdata:
                print key,type(formdata[key]),'\n'
            """

        else:
            print '获取最大页码失败'





