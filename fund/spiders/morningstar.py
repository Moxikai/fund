# -*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import re
import urlparse
import random
import copy

import scrapy
from scrapy import FormRequest,Request
from scrapy_splash import SplashRequest

class MorningstarSpider(scrapy.Spider):
    name = "morningstar"
    allowed_domains = ["cn.morningstar.com"]
    start_urls = (
        'http://cn.morningstar.com/quickrank/default.aspx',
    )
    ajax_url = 'http://cn.morningstar.com/handler/quicktake.ashx'
    query_basic = urlparse.urlparse(ajax_url)

    def parse(self, response):
        """解析基金明细数据"""
        tr_list = response.xpath('//tr[contains(@class,"Item")]')
        fund = {}
        for tr in tr_list:
            fund['code'] = tr.xpath('td[@class="msDataText"][1]/a/text()').extract_first(),
            fund['link'] = tr.xpath('td[@class="msDataText"][2]/a/@href').extract_first(),
            fund['name'] = tr.xpath('td[@class="msDataText"][2]/a/text()').extract_first()

            """转到详细页面"""
            url = urlparse.urljoin(self.start_urls[0],fund['link'])
            yield Request(url=url,
                          meta={'fund':fund},
                          callback=self.parseBasic)

        """转到列表下一页"""
        """获取总页码"""
        javascript = response.xpath('//a[contains(text(),">>")]/@href').extract()
        pattern = re.compile("'(\d{1,})'")
        total = pattern.findall(javascript[-1])
        if total:
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

        else:
            print '获取最大页码失败'

    def parseDetail(self,response):
        """解析详细数据"""
        div = response.xpath('//div[@id="qt_base"]')
        unitNet = div.xpath('/ul[@class="nav"]/li[@class="n"]/span/text()').extract_first() #净值
        unitNetDate = div.xpath('/ul[@class="nav"]/li[@class="date"]/text()').extract_first() #净值日期
        li = div.xpath('/ul[@class="change"]/li[@class="n"]')
        dailyVaritionOfNet_c = li.xpath('/span[@class="c"]/text()').extract_first() #净值变动值
        dailyVaritionOfNet_p = li.xpath('/span[@class="p"]/text()').extract_first() #净值变动率
        #补充基本信息
        info = response.xpath('//div[@id="qt_base"]/ul[@class="info"]')
        type = info.xpath('/li[@class="l"]/span[@class="category"]/text()').extract_first()
        #成立日期
        inceptionDate = info.xpath('/li[@class="m"]/span[@class="inception"]/text()').extract_first()
        #开发日期
        startDate = info.xpath('/li[@class="m"]/span[@class="start"]/text()').extract_first()
        #上市日期
        tradingDate = info.xpath('/li/span[@class="tradingdate"]/text()').extract_first()
        #申购状态
        subscribe = info.xpath('/li/span[@class="subscribe"]/text()').extract_first()
        #赎回状态
        redeem = info.xpath('/li/span[@class="redeem"]/text()').extract_first()
        #总资产
        asset = info.xpath('/li/span[@class="asset"]/text()').extract_first()
        #最低投资额
        min = info.xpath('/li/span[@class="min"]/text()').extract_first()
        #上市交易所
        stockExchange = info.xpath('/li/span[@class="front"][1]/text()').extract_first()
        #前端收费
        frontFee = info.xpath('/li/span[@class="front"][2]/text()').extract_first()
        #后端收费
        deferFee = info.xpath('/li/span[@class="defer"]/text()').extract_first()

        fcid = response.xpath('//input[@id="qt_fcid"]/@value').extract_first()

        """获取传递的值"""
        fund = response.meta
        fund['type'] = type
        fund['unitNetDate'] = unitNetDate
        fund['unitNet'] = unitNet
        fund['dailyVaritionOfNet_c'] = dailyVaritionOfNet_c
        fund['dailyVaritionOfNet_p'] = dailyVaritionOfNet_p
        fund['inceptionDate'] = inceptionDate
        fund['startDate'] = startDate
        fund['tradingDate'] = tradingDate
        fund['subscribe'] = subscribe
        fund['redeem'] = redeem
        fund['asset'] = asset
        fund['min'] = min
        fund['stockExchange'] = stockExchange
        fund['frontFee'] = frontFee
        fund['deferFee'] = deferFee
        fund['fcid'] = fcid


        """业绩回报"""
        #设置查询参数
        query = 'command=%s&fcid=%s&randomid=%s'%('return',fcid,random.random())
        query0 = copy.deepcopy(self.query_basic)
        query0.query = query
        url = urlparse.urlunparse(query0)
        yield Request(url=url,
                      meta={'fund':fund},
                      callback=self.parseFee,)

    def parseReturn(self,response):
        """获取回报数据，请求json"""
        fund = response.meta['fund']
        fund['current'] = response.body
        """转到费用"""
        query = 'command=%s&fcid=%s&randomid=%s' % ('fee', fund['fcid'], random.random())
        query0 = copy.deepcopy(self.query_basic)
        query0.query = query
        url = urlparse.urlunparse(query0)
        yield Request(url=url,
                      meta={'fund':fund},
                      callback=self.parseFee)


    def parseFee(self,response):
        """获取费用数据，请求json"""
        fund = response.meta['fund']
        fund['fee'] = response.body
        """转到费用"""
        query = 'command=%s&fcid=%s&randomid=%s' % ('agency', fund['fcid'], random.random())
        query0 = copy.deepcopy(self.query_basic)
        query0.query = query
        url = urlparse.urlunparse(query0)
        yield Request(url=url,
                      meta={'fund': fund},
                      callback=self.parseAgency)

    def parseAgency(self,response):
        """获取基金销售机构"""
        fund = response.meta['fund']
        fund['agency'] = response.body
        """转到费用"""
        query = 'command=%s&fcid=%s&randomid=%s' % ('portfolio', fund['fcid'], random.random())
        query0 = copy.deepcopy(self.query_basic)
        query0.query = query
        url = urlparse.urlunparse(query0)
        yield Request(url=url,
                      meta={'fund': fund},
                      callback=self.parsePortfolio)

    def parsePortfolio(self,response):
        """获取行业分布信息"""
        fund = response.meta['fund']
        fund['portfolio'] = response.body
        """转到费用"""
        query = 'command=%s&fcid=%s&randomid=%s' % ('manage', fund['fcid'], random.random())
        query0 = copy.deepcopy(self.query_basic)
        query0.query = query
        url = urlparse.urlunparse(query0)
        yield Request(url=url,
                      meta={'fund': fund},
                      callback=self.parseManage)

    def parseManage(self,response):
        """获取管理信息，基金经理"""
        fund = response.meta['fund']
        fund['manage'] = response.body
        """转到费用"""
        query = 'command=%s&fcid=%s&randomid=%s' % ('dividend', fund['fcid'], random.random())
        query0 = copy.deepcopy(self.query_basic)
        query0.query = query
        url = urlparse.urlunparse(query0)
        yield Request(url=url,
                      meta={'fund': fund},
                      callback=self.parseDividend)

    def parseDividend(self,response):
        """获取分红拆分信息"""
        fund = response.meta['fund']
        fund['dividend'] = response.body
        """转到费用"""
        query = 'command=%s&fcid=%s&randomid=%s' % ('performance', fund['fcid'], random.random())
        query0 = copy.deepcopy(self.query_basic)
        query0.query = query
        url = urlparse.urlunparse(query0)
        yield Request(url=url,
                      meta={'fund': fund},
                      callback=self.parsePerformance)

    def parsePerformance(self,response):
        """获取表现数据"""
        fund = response.meta['fund']
        fund['performance'] = response.body
        """转到费用"""
        query = 'command=%s&fcid=%s&randomid=%s' % ('rating', fund['fcid'], random.random())
        query0 = copy.deepcopy(self.query_basic)
        query0.query = query
        url = urlparse.urlunparse(query0)
        yield Request(url=url,
                      meta={'fund': fund},
                      callback=self.parseRating)

    def parseRating(self,response):
        """获取风险评价数据"""
        fund = response.meta['fund']
        fund['performance'] = response.body
        """转到费用"""
        yield fund







