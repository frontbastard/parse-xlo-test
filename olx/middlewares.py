# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

# useful for handling different item types with a single interface


import asyncio
import random
import ssl

import aiohttp
from scrapy import signals
from scrapy.exceptions import NotConfigured


class OlxSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class OlxDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class FastRotateProxyMiddleware:
    def __init__(
        self, proxy_url, test_url, max_concurrent_checks, check_timeout
    ):
        self.proxy_url = proxy_url
        self.test_url = test_url
        self.max_concurrent_checks = max_concurrent_checks
        self.check_timeout = check_timeout
        self.proxies = []
        self.working_proxies = set()

    @classmethod
    def from_crawler(cls, crawler):
        proxy_url = crawler.settings.get("PROXY_URL")
        test_url = crawler.settings.get(
            "PROXY_TEST_URL", "http://httpbin.org/ip"
        )
        max_concurrent_checks = crawler.settings.get(
            "PROXY_MAX_CONCURRENT_CHECKS", 100
        )
        check_timeout = crawler.settings.get("PROXY_CHECK_TIMEOUT", 2)

        if not proxy_url:
            raise NotConfigured

        middleware = cls(
            proxy_url, test_url, max_concurrent_checks, check_timeout
        )
        crawler.signals.connect(
            middleware.spider_opened, signal=signals.spider_opened
        )
        return middleware

    async def fetch_proxies(self):
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=ssl_context)
        ) as session:
            async with session.get(self.proxy_url) as response:
                if response.status == 200:
                    text = await response.text()
                    self.proxies = [
                        line.strip()
                        for line in text.split('\n')
                        if line.strip()
                    ]

    async def check_proxy(self, proxy):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.test_url, proxy=f"http://{proxy}",
                    timeout=self.check_timeout
                ) as response:
                    if response.status == 200:
                        self.working_proxies.add(proxy)
        except:
            pass

    async def check_all_proxies(self):
        tasks = []
        sem = asyncio.Semaphore(self.max_concurrent_checks)

        async def bounded_check(proxy):
            async with sem:
                await self.check_proxy(proxy)

        for proxy in self.proxies:
            task = asyncio.ensure_future(bounded_check(proxy))
            tasks.append(task)

        await asyncio.gather(*tasks)

    async def initialize_proxies(self):
        await self.fetch_proxies()
        await self.check_all_proxies()
        print(
            f"Found {len(self.working_proxies)} proxies from {len(self.proxies)}"
        )

    def spider_opened(self, spider):
        asyncio.get_event_loop().run_until_complete(self.initialize_proxies())

    def process_request(self, request, spider):
        if self.working_proxies:
            proxy = random.choice(list(self.working_proxies))
            request.meta["proxy"] = f"http://{proxy}"
