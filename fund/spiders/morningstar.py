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
from scrapy.utils.response import get_base_url
from scrapy.utils.url import urljoin_rfc
from bs4 import BeautifulSoup

class MorningstarSpider(scrapy.Spider):
    name = "morningstar"
    allowed_domains = ["cn.morningstar.com"]
    start_urls = (
        'http://cn.morningstar.com/quickrank/default.aspx',
    )
    ajax_url = 'http://cn.morningstar.com/handler/quicktake.ashx'
    query_basic = urlparse.urlparse(ajax_url)
    page = 1
    pageCount = 2

    def parse(self, response):
        """解析基金明细数据"""

        tr_list = response.xpath('//tr[contains(@class,"Item")]')
        fund = {}
        """
        for tr in tr_list:
            fund['code'] = tr.xpath('td[@class="msDataText"][1]/a/text()').extract(),
            link = tr.xpath('td[@class="msDataText"][2]/a/@href').extract(),
            fund['name'] = tr.xpath('td[@class="msDataText"][2]/a/text()').extract(),
            print link,type(link)
            url = urlparse.urljoin(get_base_url(response),link)
            print url,
            yield Request(url=url,
                          meta={'fund':fund},
                          callback=self.parseBasic)
        """
        soup = BeautifulSoup(response.body,'html.parser')
        tr_list = soup.find_all('tr',class_= "gridItem" or "gridAlternateItem")
        for tr in tr_list:
            fund['code'] = tr.find('td',class_="msDataText").a.get_text()
            fund['link'] = tr.find_all('td',class_="msDataText")[1].a.get('href')
            fund['name'] = tr.find_all('td',class_="msDataText")[1].a.get_text()
            #print fund['code'],fund['link'],fund['name']
            url = urlparse.urljoin(self.start_urls[0],fund['link']) #相对路径转换到绝对路径
            yield Request(url=url,meta={'fund':fund},callback=self.parseBasic)


        """转到列表下一页"""
        """获取总页码"""
        formdata ={}
        if self.page == 1:
            """只计算一次最大页数"""
            javascript = soup.find('div',attrs={'id':'ctl00_cphMain_AspNetPager1'}).find_all('a')[-1].get('href')
            pattern = re.compile("'(\d{1,})'")
            self.pageCount = pattern.findall(javascript)[0]
            print '总页码是----------------%s----------------'%(self.pageCount)
            self.page += 1

        elif self.page > 1 and self.page < self.pageCount:
            #页码增加1
            self.page += 1
        if self.page <= self.pageCount:
            """获取下一页post数据"""
            formdata['__EVENTTARGET'] = 'ctl00$cphMain$AspNetPager1'
            formdata['__EVENTARGUMENT'] = str(self.page)
            formdata['__VIEWSTATE'] = soup.find('input',attrs={'type':"hidden",'name':"__VIEWSTATE"}).get('value')
            formdata['__EVENTVALIDATION'] = soup.find('input',attrs={'type':'hidden','name':'__EVENTVALIDATION'}).get('value')
            formdata['__LASTFOCUS'] = ''
            formdata['ctl00$cphMain$ddlCompany'] = ''
            formdata['ctl00$cphMain$ddlPortfolio'] = ''
            formdata['ctl00$cphMain$ddlWatchList'] = ''
            formdata['ctl00$cphMain$txtFund'] = u'基金名称'
            formdata['ctl00$cphMain$ddlPageSite'] = '25'
            print '当前页码为---------%s------------'%(self.page)
            yield FormRequest(url=self.start_urls[0], formdata=formdata, callback=self.parse)
        else:
            print '已经达到最大页码'



    def parseBasic(self,response):
        """解析详细数据"""
        soup = BeautifulSoup(response.body,'html.parser')
        div = soup.find('div',attrs={'id':"qt_base"})
        ul = div.find('ul',class_="nav") #中间节点

        unitNet = ul.find('li',class_="n").span.get_text() #净值
        unitNetDate = ul.find('li',class_="date").get_text() #净值日期

        li = div.find('ul',class_="change").find('li',class_="n") #中间节点
        dailyVaritionOfNet_c = li.find('span',class_="c").get_text()
        dailyVaritionOfNet_p = li.find('span',class_="p").get_text()

        li_list = div.find('ul',class_="info").find_all('li')#中间节点
        type = li_list[0].find('span').get_text() #类型
        inceptionDate = li_list[1].find('span').get_text() #成立日期
        startDate = li_list[2].find('span').get_text() #开发日期
        tradingDate = li_list[3].find('span').get_text() # 上市日期
        subscribe = li_list[4].find('span').get_text() # 申购状态
        redeem = li_list[5].find('span').get_text() #赎回状态
        asset = li_list[7].find('span').get_text() #总资产
        minunit = li_list[8].find('span').get_text() #最小投资额
        stockExchange = li_list[9].find('span').get_text() # 交易所
        frontFee = li_list[10].find('span').get_text() # 前端收费
        deferFee = li_list[11].find('span').get_text() # 后端收费
        fcid = soup.find('input',attrs={'id':'qt_fcid'}).get('value') #fcid

        fund = response.meta['fund'] # 获取粘性参数
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
        fund['min'] = minunit
        fund['stockExchange'] = stockExchange
        fund['frontFee'] = frontFee
        fund['deferFee'] = deferFee
        fund['fcid'] = fcid

        #yield fund
        """业绩回报"""
        #设置查询参数
        query = 'command=%s&fcid=%s&randomid=%s'%('return',fcid,random.random())
        url = urlparse.urlunparse(('http',
                                   'cn.morningstar.com',
                                   '/handler/quicktake.ashx',
                                   '',
                                   query,
                                   ''))
        yield Request(url=url,
                      meta={'fund':fund},
                      callback=self.parseFee,)

    def parseReturn(self,response):
        """获取回报数据，请求json"""
        fund = response.meta['fund']
        fund['current'] = response.body
        """转到费用"""
        query = 'command=%s&fcid=%s&randomid=%s' % ('fee', fund['fcid'], random.random())
        url = urlparse.urlunparse(('http',
                                   'cn.morningstar.com',
                                   '/handler/quicktake.ashx',
                                   '',
                                   query,
                                   ''))


    def parseFee(self,response):
        """获取费用数据，请求json"""
        fund = response.meta['fund']
        fund['fee'] = response.body
        """转到费用"""
        query = 'command=%s&fcid=%s&randomid=%s' % ('agency', fund['fcid'], random.random())
        url = urlparse.urlunparse(('http',
                                   'cn.morningstar.com',
                                   '/handler/quicktake.ashx',
                                   '',
                                   query,
                                   ''))
        yield Request(url=url,
                      meta={'fund': fund},
                      callback=self.parseAgency)

    def parseAgency(self,response):
        """获取基金销售机构"""
        fund = response.meta['fund']
        fund['agency'] = response.body
        """转到费用"""
        query = 'command=%s&fcid=%s&randomid=%s' % ('portfolio', fund['fcid'], random.random())
        url = urlparse.urlunparse(('http',
                                   'cn.morningstar.com',
                                   '/handler/quicktake.ashx',
                                   '',
                                   query,
                                   ''))
        yield Request(url=url,
                      meta={'fund': fund},
                      callback=self.parsePortfolio)

    def parsePortfolio(self,response):
        """获取行业分布信息"""
        fund = response.meta['fund']
        fund['portfolio'] = response.body
        """转到费用"""
        query = 'command=%s&fcid=%s&randomid=%s' % ('manage', fund['fcid'], random.random())
        url = urlparse.urlunparse(('http',
                                   'cn.morningstar.com',
                                   '/handler/quicktake.ashx',
                                   '',
                                   query,
                                   ''))
        yield Request(url=url,
                      meta={'fund': fund},
                      callback=self.parseManage)

    def parseManage(self,response):
        """获取管理信息，基金经理"""
        fund = response.meta['fund']
        fund['manage'] = response.body
        """转到费用"""
        query = 'command=%s&fcid=%s&randomid=%s' % ('dividend', fund['fcid'], random.random())
        url = urlparse.urlunparse(('http',
                                   'cn.morningstar.com',
                                   '/handler/quicktake.ashx',
                                   '',
                                   query,
                                   ''))
        yield Request(url=url,
                      meta={'fund': fund},
                      callback=self.parseDividend)

    def parseDividend(self,response):
        """获取分红拆分信息"""
        fund = response.meta['fund']
        fund['dividend'] = response.body
        """转到费用"""
        query = 'command=%s&fcid=%s&randomid=%s' % ('performance', fund['fcid'], random.random())
        url = urlparse.urlunparse(('http',
                                   'cn.morningstar.com',
                                   '/handler/quicktake.ashx',
                                   '',
                                   query,
                                   ''))
        yield Request(url=url,
                      meta={'fund': fund},
                      callback=self.parsePerformance)

    def parsePerformance(self,response):
        """获取表现数据"""
        fund = response.meta['fund']
        fund['performance'] = response.body
        """转到费用"""
        query = 'command=%s&fcid=%s&randomid=%s' % ('rating', fund['fcid'], random.random())
        url = urlparse.urlunparse(('http',
                                   'cn.morningstar.com',
                                   '/handler/quicktake.ashx',
                                   '',
                                   query,
                                   ''))
        yield Request(url=url,
                      meta={'fund': fund},
                      callback=self.parseRating)

    def parseRating(self,response):
        """获取风险评价数据"""
        fund = response.meta['fund']
        fund['performance'] = response.body
        """转到费用"""
        yield fund







