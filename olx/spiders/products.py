import scrapy
from scrapy.http import FormRequest
from olx.spiders.utils import parse_date, get_price_details


class ProductsSpider(scrapy.Spider):
    name = "products"
    allowed_domains = ["www.olx.ua"]
    start_urls = ["https://www.olx.ua/list/"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pages_crawled = 0
        self.max_pages = 5

    def parse(self, response):
        self.pages_crawled += 1
        self.logger.info(f"Parsing page {self.pages_crawled}")

        for product in response.css('div[data-cy="l-card"]'):
            url = product.css('[data-cy="ad-card-title"] a::attr(href)').get()
            if url:
                yield response.follow(url, self.parse_product)
            else:
                self.logger.warning("Found product without URL")

        if self.pages_crawled < self.max_pages:
            next_page = response.css(
                'a[data-cy="pagination-forward"]::attr(href)'
            ).get()
            if next_page:
                self.logger.info(f"Moving to page {self.pages_crawled + 1}")
                yield response.follow(next_page, self.parse)
            else:
                self.logger.info("No more pages available")

    def parse_product(self, response):
        yield {
            "title": response.css('[data-cy="ad_title"] h4::text').get(),
            "price": get_price_details(
                response.css(
                    '[data-testid="ad-price-container"] h3::text'
                ).get()
            ),
            "phone_number": self.get_phone_number(response),
            "posted_at": parse_date(
                response.css('[data-cy="ad-posted-at"]::text').get()
            ),
            "image": response.css(
                '.swiper-zoom-container img::attr(src)'
            ).get(),
            "description": response.css(
                '[data-cy="ad_description"] h3 + div::text'
            ).get(),
            "parameters": response.css(
                '.css-41yf00 > ul p::text, .css-41yf00 > ul p span::text, .css-41yf00 > ul li::text'
            ).getall(),
            "views_qty": response.css(
                '[data-testid="page-view-counter"]::text'
            ).re_first(r'\d+'),
            "product_id": response.xpath(
                '//div[@data-testid="ad-footer-bar-section"]//span[contains(text(), "ID:")]//text()'
            ).re_first(r'ID:\s*(\d+)'),
        }

    def get_phone_number(self, response):
        return FormRequest.from_response(
            response,
            formdata={
                'id': response.css(
                    'button[data-cy="ad-contact-phone"]::attr(data-id)'
                ).get()
            },
            callback=self.parse_phone_number
        )

    def parse_phone_number(self, response):
        return response.json()['value']
