from scrapy.exceptions import IgnoreRequest
from scrapy.http import Response

from dvsvc_crawl import helpers
from dvsvc_crawl.spiders import get_spiders_logger

FLD_BAD_RESPONSES_ALLOWED = 10

LOGGER = get_spiders_logger()


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
