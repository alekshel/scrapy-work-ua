import re

import scrapy


class WorkuaSpider(scrapy.Spider):
    name = "workua"
    allowed_domains = ["work.ua"]
    start_urls = ["https://www.work.ua/jobs-python/"]

    @staticmethod
    def parse_vacancy(response):
        title = response.xpath('//h1[@id="h1-name"]/text()').get()

        salary = None
        currency_box = response.css(".glyphicon-hryvnia")
        if currency_box:
            salary = (
                currency_box.xpath("./following-sibling::span/text()")
                .get()
                .replace("\u202f", "")
                .replace("\xa0", "")
                .replace("\u2009", "")
            )

        job_description_html = response.css("div#job-description").extract_first()
        cleaned_html = re.sub(
            r'\s(class|id|style|...)="[^"]*"', "", job_description_html
        )
        cleaned_html = re.sub(r"[\n\r]+\s*", "", cleaned_html)
        cleaned_html = re.sub(
            r'<a\s+([^>]*\s+)?href\s*=\s*["\'](http://[^"\']*)["\']',
            r'<a \1data-not-secure-href="\2"',
            cleaned_html,
        )

        employer = (
            response.css(".glyphicon-company")
            .xpath("./following-sibling::a/span/text()")
            .get()
        )

        yield {
            "url": response.url,
            "title": title,
            "salary": salary,
            "description": cleaned_html,
            "employer": employer,
        }

    def parse(self, response):
        for card in response.css(".job-link"):
            vacancy_url = card.css(".add-bottom").xpath("./h2/a/@href").get()
            if vacancy_url is None:
                continue

            yield response.follow(vacancy_url, callback=self.parse_vacancy)

        next_page = response.css(".pagination li")[-1]
        if "disable" not in next_page.xpath("./@class").get():
            href = next_page.xpath("./a/@href").get()
            yield response.follow(href, callback=self.parse)
