import re
from datetime import datetime

import scrapy
from scrapy import Selector
from scrapy.http import Response
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from olx.spiders.utils import parse_date, extract_main_price


class ProductsSpider(scrapy.Spider):
    name = "products"
    allowed_domains = ["www.olx.ua"]
    start_urls = ["https://www.olx.ua/list/"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pages_crawled = 1
        self.driver = webdriver.Chrome()

    def close(self, reason: str):
        self.driver.close()
        return self.close(reason)

    def parse(self, response: Response, **kwargs):
        acc = 0
        for product in response.css('div[data-cy="l-card"]'):
            if acc < 3:
                yield self._parse_detail_info(response, product)
                # yield {
                #     "title": product.css(
                #         '[data-cy="ad-card-title"] h4::text'
                #     ).get(),
                # }
                acc += 1
            else:
                break
        # next_page = response.css(
        #     'a[data-cy="pagination-forward"]::attr(href)'
        # ).get()
        # if next_page and self.pages_crawled < 5:
        #     self.pages_crawled += 1
        #     yield response.follow(next_page, self.parse)

    def _parse_detail_info(
        self,
        response: Response,
        product: Selector
    ) -> dict[str, str]:
        absolute_url = response.urljoin(
            product.css('[data-cy="ad-card-title"] a::attr(href)').get()
        )
        self.driver.get(absolute_url)

        # phone
        try:
            phone_btn = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'button[data-cy="ad-contact-phone"]')
                )
            )
            phone_btn_cursor = phone_btn.value_of_css_property("cursor")

            if phone_btn_cursor == "pointer":
                phone_btn.click()

                phone_number_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, 'a[data-testid="contact-phone"]')
                    )
                )
                phone_number = phone_number_element.text
            else:
                phone_number = None
        except Exception:
            phone_number = None

        # price
        try:
            price_element = self.driver.find_element(
                By.CSS_SELECTOR, '[data-testid="ad-price-container"] h3'
            )
            price = price_element.text
        except Exception:
            price = None

        return {
            "title": product.css('[data-cy="ad-card-title"] h4::text').get(),
            "price": {
                "value": extract_main_price(price),
                "currency": "USD" if "$" in price else "UAH",
            },
            "phone_number": phone_number,
            "posted_at": product.css('[data-cy="ad-posted-at"]::text').get(),
            # "posted_at": parse_date(
            #     product.css('[data-cy="ad-posted-at"]::text').get()
            # ),
        }
