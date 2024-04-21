import logging
import re
from typing import Optional
from maxima_scrapper import maxima_search


async def search_product(message, search_text, limit,
                         offset: Optional[int] = None, category: Optional[str] = None) -> int:
    try:
        logging.info(
            f'Searching: \'{search_text}\' from user: {message.from_user.full_name} (ID:{message.from_user.id})')
        results = await maxima_search(search_text, limit, offset, category)
        if not results:
            await message.answer('Nothing found')
            return 0
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
                if result.percent is not None:
                    formatted_message = formatted_message + f'<b>{result.percent}</b>\n\n'
                if result.title is not None:
                    formatted_message = formatted_message + f'{result.title}'
                if result.date is not None:
                    formatted_message = formatted_message + f'\n\n<em>{result.date}</em>'

                await message.answer(formatted_message)
            return len(results)
    except Exception as error:
        logging.error(f'Error while searching for product \'{search_text}\': {error}')