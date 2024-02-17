import logging
from aiohttp import web
from bs4 import BeautifulSoup
from discount_wrapper import DiscountWrapper
import re
import aiohttp
import os
import asyncio
import json


async def maxima_search(search_thing, limit, offset, category):
    try:
        url = f'https://www.maxima.lv/ajax/salesloadmore'  # &limit=1&search=&offset={offset}
        params = {
            'sort_by': 'newest',
            'limit': limit,
            'search': '',
            'search1': search_thing
        }
        if offset is not None:
            params.update({'offset': offset})
        if category is not None:
            params.update({'categories[]': category})

        html_content = await fetch_html_content(url, params)

        try:
            jsons = json.loads(html_content)
            content = jsons.get('html', '')
        except ValueError:
            content = html_content
        soup = BeautifulSoup(content, 'html.parser')
        data = soup.find_all("div", class_="col-third offer-item")

    except Exception as search_exception:
        logging.error(f'Invalid search body: {search_thing}\nError: {search_exception}')
        raise ValueError(search_exception)

    try:
        scrapped_data = scrap_data(data)
    except Exception as scrap_exception:
        logging.error(f'Error while scrapping data: {scrap_exception}')
        raise ValueError(scrap_exception)
    return scrapped_data


async def fetch_html_content(url, params=None):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            return await response.text()


def scrap_data(data):
    results = []
    for dat in data:
        result = DiscountWrapper()

        img_tag = dat.find('div', class_='img').find('img')
        src_value = img_tag.get('src')
        result.image_url = src_value

        bottom = dat.find("div", class_="bottom-icon")
        paldies = dat.find("div", class_='t1 paldies-card')

        percent_wrapper = dat.find("div", class_='percents_wrapper')
        if bottom:
            percent = get_percent_spans(bottom)
            result.percent = percent
        elif paldies:
            paldies_spans = paldies.find_all('span')
            paldies_price = ''
            for paldies_span in paldies_spans:
                paldies_class = paldies_span.get('class')
                if 'value' in paldies_class:
                    paldies_price = paldies_span.text
                elif 'cents' in paldies_class:
                    paldies_price = paldies_price + ',' + paldies_span.text
                elif 'eur' in paldies_class:
                    paldies_price = paldies_price + paldies_span.text
            result.paldies_price = paldies_price
        elif percent_wrapper:
            percent = get_percent_spans(percent_wrapper)
            result.percent = percent

        new_price_div = dat.find("div", class_="t1")
        if new_price_div:
            new_price_spans = new_price_div.find_all("span")
            new_price = ''
            for new_price_span in new_price_spans:
                paldies_class = new_price_span.get("class")
                if 'value' in paldies_class:
                    new_price = new_price_span.text
                elif 'cents' in paldies_class:
                    new_price = new_price + ',' + new_price_span.text
                elif 'eur' in paldies_class:
                    new_price = new_price + new_price_span.text
            result.new_price = new_price

        old_price_div = dat.find("div", class_="t3")
        if old_price_div:
            old_price_spans = old_price_div.find_all("span")
            old_price = ''
            for old_price_span in old_price_spans:
                old_price_class = old_price_span.get("class")
                if 'value' in old_price_class:
                    old_price = old_price_span.text
                elif 'cents' in old_price_class:
                    old_price = old_price + ',' + old_price_span.text
                elif 'eur' in old_price_class:
                    old_price = old_price + old_price_span.text
            result.old_price = old_price

        title_div = dat.find("div", class_='title')
        result.title = title_div.text

        date_interval_divs = dat.find_all("div", attrs={"data-dates-interval": True})
        if date_interval_divs:
            for date_div in date_interval_divs:
                date_interval = date_div["data-dates-interval"]
                result.date = date_interval
        results.append(result)
    return results


def get_percent_spans(divs):
    div_spans = divs.find_all("span")
    div_obj = ''
    for span in div_spans:
        classes = span.get("class")
        if 'sign' in classes:
            div_obj = span.text
        elif 'value' in classes:
            div_obj = div_obj + span.text
        elif 'per' in classes:
            div_obj = div_obj + span.text
    return div_obj
