import re
import time
from lxml import etree

from utils import getAmazonDomain, LANG_CODE, TIME_CODE, STANDARD_TIME, REVIEW_HELPFUL, REVIEW_COUNTRY

STARS = r'(\d+)'
HELPFUL = r'(\d+)'


class AmazonDispose:
    def __init__(self, AmazonData, Country, ASIN):
        self.Country = Country
        self.ASIN = ASIN
        self.selector = etree.HTML(AmazonData)

    def dispose(self):
        reviewAll = []
        reviewData = self.selector.xpath('//div[@data-hook="review"]')
        if len(reviewData) <= 0:
            return None
        for review in reviewData:
            reviewRow = {}
            reviewDate = review.xpath('div/div/span[@data-hook="review-date"]//text()')
            reviewCountry = review.xpath('div/div/span[@data-hook="published-on-amzn-text"]//text()') \
                if self.Country == 'CN' else reviewDate
            reviewHref = review.xpath('div/div/div[2]/a[@data-hook="review-title"]/@href')
            reviewTitle = review.xpath('div/div/div[2]/a[@data-hook="review-title"]/span//text()')
            reviewStrip = review.xpath('div/div/div[3]/a[@data-hook="format-strip"]//text()')
            reviewVP = review.xpath('div/div/div[3]/span/a/span[@data-hook="avp-badge"]')

            reviewVP = 'vp' if reviewVP else '非vp'

            reviewBuyer = review.xpath('div/div/div[@data-hook="genome-widget"]/a/@href')
            reviewBuyerName = \
                review.xpath('div/div/div[@data-hook="genome-widget"]/a/div[@class="a-profile-content"]/span//text()')
            reviewStars = \
                review.xpath('div/div/div[2]/a[@class="a-link-normal"]/i[@data-hook="review-star-rating"]/@class')
            reviewStars = re.search(STARS, self.getData(reviewStars))

            reviewStars = reviewStars.group(1) if reviewStars else ''

            reviewHelpful = review.xpath('div/div/div[contains(@class, "review-comments")]/div'
                                         '/span[@data-hook="review-voting-widget"]/div[1]'
                                         '/span[@data-hook="helpful-vote-statement"]//text()')
            re_review_helpful = re.search(HELPFUL, self.getData(reviewHelpful))

            reviewHelpful = re_review_helpful.group(1) if re_review_helpful else self.get_helpful(reviewHelpful)

            reviewContent = review.xpath('div/div/div[4]/span[@data-hook="review-body"]//text()')
            # print(self.get_date(reviewDate))
            reviewRow['asin'] = self.ASIN
            reviewRow['date'] = self.get_date(reviewDate)
            reviewRow['href'] = self.getURLData(reviewHref)
            reviewRow['title'] = self.getData(reviewTitle)
            reviewRow['format'] = self.getData(reviewStrip)
            reviewRow['vp'] = reviewVP
            reviewRow['buyer'] = self.getURLData(reviewBuyer)
            reviewRow['name'] = self.getData(reviewBuyerName)
            reviewRow['stars'] = reviewStars
            reviewRow['content'] = self.getData(reviewContent)
            reviewRow['helpful'] = reviewHelpful
            reviewRow['review_country'] = self.get_country(reviewCountry)
            reviewAll.append(reviewRow)
        return reviewAll

    def isNextPage(self):
        next_page = self.selector.xpath('//li[contains(@class, "a-last")]/@class')
        if next_page:
            return False if 'a-disabled' in next_page else True
        else:
            return False

    def getData(self, data):
        return ''.join(data).strip().replace('\n', '') if data else ''

    def getURLData(self, data):
        return '%s%s' % (getAmazonDomain(self.Country), self.getData(data)) if data else ''

    def get_date(self, data):
        date = self.getData(data)
        try:
            date = date.replace(' ', '')
            time_format = TIME_CODE[self.Country]
            if type(time_format) == dict:
                if 'replace' in time_format:
                    if type(time_format['replace']) == list:
                        for replace_item in time_format['replace']:
                            date = re.sub(self.re_remove_spaces(replace_item), '', date)
                            # date = date.replace(replace_item.replace(' ', ''), '')
                    else:
                        date = re.sub(self.re_remove_spaces(time_format['replace']), '', date)
                        # date = date.replace(time_format['replace'].replace(' ', ''), '')
                if 'MapMonth' in time_format:
                    for item in time_format['MapMonth']:
                        date = date.replace(item, time_format['MapMonth'][item])
                time_format = time_format['format']
            time_struct = time.strptime(date, time_format)
            return time.strftime(STANDARD_TIME, time_struct)
        except (TypeError, ValueError, SyntaxError) as e:
            print(e)
            return date

    def get_helpful(self, data):
        helpful_data = self.getData(data).lower()
        helpful = REVIEW_HELPFUL[self.Country]
        return 1 if helpful and helpful_data.find(helpful.lower()) > -1 else 0

    def get_country(self, data):
        country_data = self.getData(data)
        re_country = REVIEW_COUNTRY[self.Country]
        if re_country:
            country_data = re.search(re_country, country_data)
            return country_data.group(1) if country_data else ''
        return ''

    def get_selector(self):
        return self.selector

    def is_lang(self):
        lang = self.selector.xpath('//select[@id="language-type-dropdown"]')
        if not lang:
            return False
        for item in lang:
            param = item.xpath('option[@selected]/@value')
        for (key, value) in LANG_CODE.items():
            if value == self.getData(param) and key == 'CN':
                return True
        return False

    @staticmethod
    def re_remove_spaces(data):
        return re.sub(r' ', '', data)