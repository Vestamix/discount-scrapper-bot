import requests
from bs4 import BeautifulSoup
import telebot

import config


def maxima_search(search_thing):
    url = f'https://www.maxima.lv/ajax/salesloadmore?sort_by=newest&search={search_thing}'  # &limit=1&search=
    response = requests.get(url)
    html_content = response.text
    soup = BeautifulSoup(html_content, 'html.parser')
    data = soup.find_all("div", class_="col-third offer-item")
    return scrap_data(data)


def scrap_data(data):
    results = []
    for dat in data:
        # print(dat)
        result = ''
        bottom = dat.find("div", class_="bottom-icon")
        paldies = dat.find("div", class_='t1 paldies-card')
        percent_wrapper = dat.find("div", class_='percents_wrapper')
        if bottom:
            obj = get_percent_spans(bottom)
            result = result + obj + '\n'
        elif paldies:
            paldies_spans = paldies.find_all('span')
            paldies_obj = ''
            for span in paldies_spans:
                classes = span.get('class')
                if 'value' in classes:
                    paldies_obj = span.text
                elif 'cents' in classes:
                    paldies_obj = paldies_obj + ',' + span.text
                elif 'eur' in classes:
                    paldies_obj = paldies_obj + span.text
            result = result + paldies_obj + '\n'
        elif percent_wrapper:
            obj = get_percent_spans(percent_wrapper)
            result = result + obj + '\n'
        t1 = dat.find("div", class_="t1")
        if t1:
            spans = t1.find_all("span")
            t1_obj = ''
            for span in spans:
                classes = span.get("class")
                if 'value' in classes:
                    t1_obj = span.text
                elif 'cents' in classes:
                    t1_obj = t1_obj + ',' + span.text
                elif 'eur' in classes:
                    t1_obj = t1_obj + span.text
            result = result + t1_obj + '\n'
        t3 = dat.find("div", class_="t3")
        if t3:
            spans = t3.find_all("span")
            t1_obj = ''
            for span in spans:
                classes = span.get("class")
                if 'value' in classes:
                    t1_obj = span.text
                elif 'cents' in classes:
                    t1_obj = t1_obj + ',' + span.text
                elif 'eur' in classes:
                    t1_obj = t1_obj + span.text
            result = result + t1_obj + '\n'

        title = dat.find("div", class_='title')
        result = result + title.text + '\n'
        date_interval_divs = dat.find_all("div", attrs={"data-dates-interval": True})
        if date_interval_divs:
            for div in date_interval_divs:
                date_interval = div["data-dates-interval"]
                result = result + date_interval + '\n'
        results.append(result)
    return results


def get_percent_spans(divs):
    global span, classes
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


bot = telebot.TeleBot(config.TOKEN)


@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_message(
        message.chat.id,
        'Hello! This is discount search bot. \n'
        'Currently it works only with maxima offers. \n'
        'To use it, just type product name or type (you can use EN letters e.g. Kaku bariba)\n'
    )


@bot.message_handler(content_types=['text'])
def search(message):
    results = maxima_search(message.text)
    if not results:
        bot.send_message(message.chat.id, 'Nothing found')
    else:
        for result in results:
            bot.send_message(message.chat.id, result)


bot.infinity_polling()
