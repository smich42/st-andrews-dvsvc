# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html


from scrapy.exceptions import IgnoreRequest
from scrapy.http import Response

from dvsvc_crawl import helpers
from dvsvc_crawl.spiders import get_dvsvc_logger

FLD_BAD_RESPONSES_ALLOWED = 10

LOGGER = get_dvsvc_logger()


class DvsvcBlacklistMiddleware:
    def __init__(self):
        self.fld_blacklist = set()
        self.fld_bad_responses = {}

    def process_request(self, request, spider):
        fld = helpers.get_fld(request.url)

        if fld in self.fld_blacklist:
            raise IgnoreRequest(f"Ignoring request to blacklisted FLD: {request.url}")
        return None

    def process_response(self, request, response, spider):
        fld = helpers.get_fld(request.url)

        if response.status != 200 and fld not in self.fld_blacklist:
            # Increment counter for non-200 responses
            if fld not in self.fld_bad_responses:
                self.fld_bad_responses[fld] = 1
            else:
                self.fld_bad_responses[fld] += 1

            if self.fld_bad_responses[fld] >= FLD_BAD_RESPONSES_ALLOWED:
                self.fld_blacklist.add(fld)
                LOGGER.info(f"Blacklisted FLD: {fld}")

        return response

    def process_exception(self, request, exception, spider):
        if isinstance(exception, IgnoreRequest):
            # Propagate rudimentary response to spider so it may be processed
            return Response(url=request.url, status=400, request=request)
        # Non-IgnoreRequest exceptions will be propagated to other middleware
        return None


# class DvsvcCrawlSpiderMiddleware:
#     # Not all methods need to be defined. If a method is not defined,
#     # scrapy acts as if the spider middleware does not modify the
#     # passed objects.

#     @classmethod
#     def from_crawler(cls, crawler):
#         # This method is used by Scrapy to create your spiders.
#         s = cls()
#         crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
#         return s

#     def process_spider_input(self, response, spider):
#         # Called for each response that goes through the spider
#         # middleware and into the spider.

#         # Should return None or raise an exception.
#         return None

#     def process_spider_output(self, response, result, spider):
#         # Called with the results returned from the Spider, after
#         # it has processed the response.

#         # Must return an iterable of Request, or item objects.
#         for i in result:
#             yield i

#     def process_spider_exception(self, response, exception, spider):
#         # Called when a spider or process_spider_input() method
#         # (from other spider middleware) raises an exception.

#         # Should return either None or an iterable of Request or item objects.
#         pass

#     def process_start_requests(self, start_requests, spider):
#         # Called with the start requests of the spider, and works
#         # similarly to the process_spider_output() method, except
#         # that it doesn’t have a response associated.

#         # Must return only requests (not items).
#         for r in start_requests:
#             yield r

#     def spider_opened(self, spider):
#         spider.logger.info("Spider opened: %s" % spider.name)


# class DvsvcCrawlDownloaderMiddleware:
#     # Not all methods need to be defined. If a method is not defined,
#     # scrapy acts as if the downloader middleware does not modify the
#     # passed objects.

#     @classmethod
#     def from_crawler(cls, crawler):
#         # This method is used by Scrapy to create your spiders.
#         s = cls()
#         crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
#         return s

#     def process_request(self, request, spider):
#         # Called for each request that goes through the downloader
#         # middleware.

#         # Must either:
#         # - return None: continue processing this request
#         # - or return a Response object
#         # - or return a Request object
#         # - or raise IgnoreRequest: process_exception() methods of
#         #   installed downloader middleware will be called
#         return None

#     def process_response(self, request, response, spider):
#         # Called with the response returned from the downloader.

#         # Must either;
#         # - return a Response object
#         # - return a Request object
#         # - or raise IgnoreRequest
#         return response

#     def process_exception(self, request, exception, spider):
#         # Called when a download handler or a process_request()
#         # (from other downloader middleware) raises an exception.

#         # Must either:
#         # - return None: continue processing this exception
#         # - return a Response object: stops process_exception() chain
#         # - return a Request object: stops process_exception() chain
#         pass

#     def spider_opened(self, spider):
#         spider.logger.info("Spider opened: %s" % spider.name)
