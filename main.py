import re
import aiohttp
import os
import asyncio
import logging
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.types import Message
from aiogram.filters import Command

logging.basicConfig(level=logging.INFO)
logging.info('Initializing router')
router = Router()
logging.info(f'Router initialized: {router.name}')
bot = None
dp = None


async def main():
    global bot, dp
    logging.info('Initializing bot')
    try:
        token = os.environ.get("API_KEY")
        bot = Bot(token=token, parse_mode='HTML')
        dp = Dispatcher()
        dp.include_router(router)
        logging.info(f'Bot initialized with id: {bot.id}')
    except Exception as e:
        logging.error(f'Failed to initialize bot: {e}')

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logging.info('Starting polling')
        await dp.start_polling(bot)
        logging.info('Polling started')
    except Exception as e:
        logging.error(f'Error with starting polling: {e}')


class DiscountWrapper:
    def __init__(self):
        self.title = None
        self.old_price = None
        self.new_price = None
        self.paldies_price = None
        self.percent = None
        self.image_url = None
        self.date = None

    def set_title(self, title):
        self.title = title

    def set_old_price(self, old_price):
        self.old_price = old_price

    def set_new_price(self, new_price):
        self.new_price = new_price

    def set_paldies_price(self, paldies_price):
        self.paldies_price = paldies_price

    def set_percent(self, percent):
        self.percent = percent

    def set_image_url(self, image_url):
        self.image_url = image_url

    def set_date(self, date):
        self.date = date


async def fetch_html_content(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()


async def maxima_search(search_thing):
    try:
        url = f'https://www.maxima.lv/ajax/salesloadmore?sort_by=newest&search={search_thing}'  # &limit=1&search=
        html_content = fetch_html_content(url)
        soup = BeautifulSoup(html_content, 'html.parser')
        data = soup.find_all("div", class_="col-third offer-item")
    except Exception as e:
        logging.error(f'Invalid search body: {search_thing}\nError: {e}')
        raise ValueError(e)

    try:
        scrapped_data = scrap_data(data)
    except Exception as e:
        logging.error(f'Error while scrapping data: {e}')
        raise ValueError(e)
    return scrapped_data


def scrap_data(data):
    results = []
    for dat in data:
        # print(dat)
        result = DiscountWrapper()

        img_tag = dat.find('div', class_='img').find('img')
        src_value = img_tag.get('src')
        result.set_image_url(src_value)

        bottom = dat.find("div", class_="bottom-icon")
        paldies = dat.find("div", class_='t1 paldies-card')

        percent_wrapper = dat.find("div", class_='percents_wrapper')
        if bottom:
            percent = get_percent_spans(bottom)
            result.set_percent(percent)
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
            result.set_paldies_price(paldies_price)
        elif percent_wrapper:
            percent = get_percent_spans(percent_wrapper)
            result.set_percent(percent)

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
            result.set_new_price(new_price)

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
            result.set_old_price(old_price)

        title_div = dat.find("div", class_='title')
        result.set_title(title_div.text)

        date_interval_divs = dat.find_all("div", attrs={"data-dates-interval": True})
        if date_interval_divs:
            for date_div in date_interval_divs:
                date_interval = date_div["data-dates-interval"]
                result.set_date(date_interval)
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


@router.message(Command('start'))
async def start_command(message: types.Message):
    logging.info('Received start command')
    await message.answer(
        'Hello! This is discount search bot. \n'
        'Currently it works only with maxima offers. \n'
        'To use it, just type product name or type (you can use EN letters e.g. Kaku bariba)\n'
    )


@router.message(F.text)
async def search(message: Message):
    search_text = message.text
    try:
        logging.info(f'Searching: \'{search_text}\' from user: {message.from_user.full_name} (ID:{message.from_user.id})')
        results = await maxima_search(search_text)
        if not results:
            await message.answer('Nothing found')
        else:
            for result in results:
                maxima_prefix = 'https://www.maxima.lv/'
                img_url = maxima_prefix + result.image_url
                cleaned_url = re.sub(r'\.png.*$', '.png', img_url)
                await message.answer_photo(cleaned_url)

                formatted_message = ''
                if result.old_price is not None:
                    formatted_message = formatted_message + f'<strike>{result.old_price}</strike>\n'
                if result.new_price is not None:
                    formatted_message = formatted_message + f'<b>{result.new_price}</b>\n\n'
                if result.title is not None:
                    formatted_message = formatted_message + f'{result.title}'
                if result.date is not None:
                    formatted_message = formatted_message + f'\n\n<em>{result.date}</em>'

                await message.answer(formatted_message)
    except Exception as error:
        logging.error(f'Error while searching for product \'{search_text}\': {error}')


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logging.error(f'Error in main: {e}')
