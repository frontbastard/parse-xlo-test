import scrapy
from scrapy.http import Response


class ProductsSpider(scrapy.Spider):
    name = "products"
    allowed_domains = ["www.olx.ua"]
    start_urls = ["https://www.olx.ua/list/"]

    def __init__(self, name: str | None = None, **kwargs):
        super().__init__(name, **kwargs)
        self.pages_crawled = 1

    def parse(self, response: Response, **kwargs):
        for product in response.css('div[data-cy="l-card"]'):
            yield {
                "title": product.css(
                    '[data-cy="ad-card-title"] h4::text'
                ).get(),
            }
        next_page = response.css(
            'a[data-cy="pagination-forward"]::attr(href)'
        ).get()
        if next_page and self.pages_crawled < 5:
            self.pages_crawled += 1
            yield response.follow(next_page, self.parse)
