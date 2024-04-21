import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.filters import Command
from aiogram.types import Message
from aiohttp import web

from categories import Category
from search_service import search_product

DEFAULT_LIMIT = 5
DEFAULT_OFFSET = 10

category_commands = {
    '/meat': Category.MEAT,
    '/veggies': Category.VEGGIES,
    '/bread': Category.BREAD,
    '/fish': Category.FISH,
    '/dairy': Category.DAIRY
}

logging.basicConfig(level=logging.INFO)
logging.info('Initializing router')
router = Router()
logging.info(f'Router initialized: {router.name}')
token = os.environ.get("API_KEY")
bot = Bot(token=token, parse_mode='HTML')
dp = Dispatcher()
dp.include_router(router)
logging.info(f'Bot initialized with id: {bot.id}')


async def set_commands():
    commands = [
        types.BotCommand(command='/start', description='Get started with bot'),
        types.BotCommand(command='/meat', description='🥩 Meat'),
        types.BotCommand(command='/veggies', description='🍅 Vegetables'),
        types.BotCommand(command='/bread', description='🍞 Bread'),
        types.BotCommand(command='/fish', description='🐟 Fish'),
        types.BotCommand(command='/dairy', description='🥛🥚 Milk and egg products')
    ]
    await bot.set_my_commands(commands)


async def health_check(request):
    logging.info('Called for healthcheck')
    return web.Response(text='Bot is healthy')


async def index(request):
    return web.Response(text='Welcome to the Discount Bot!')


app = web.Application()
app.router.add_get('/', index)
app.router.add_get('/health', health_check)


async def start_server():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    logging.info(f'Web app started at {site.name}')


async def start_bot():
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logging.info('Starting polling')
        await set_commands()
        await dp.start_polling(bot)
        logging.info('Polling started')
    except Exception as e:
        logging.error(f'Error with starting polling or web app: {e}')


async def main():
    global bot, dp
    try:
        logging.info('Starting web app')
        await start_server()
    except Exception as e:
        logging.error(f'Web app failed to start: {e}')

    logging.info('Initializing bot')
    await start_bot()


@router.message(Command('start'))
async def start_command(message: types.Message):
    logging.info('Received start command')
    await message.answer(
        'Hello! This is maxima discount search bot. \n\n'
        'Use \'☰ Menu\' button to search by categories. \n'
        'Or just type product name or type (you can use ENG letters e.g. Kaku bariba)\n'
    )


@router.message(F.text)
async def search(message: Message):
    value = message.text

    if value in category_commands:
        await search_by_category(category_commands.get(value), message)
    else:
        result_size = await search_product(message, value, limit=DEFAULT_LIMIT)

        if result_size == DEFAULT_LIMIT:
            button = types.InlineKeyboardButton(text='⏳',
                                                callback_data=f'load_more_'
                                                              f'{DEFAULT_OFFSET}_{value}_{message.message_id}')
            keyboard = types.InlineKeyboardMarkup(inline_keyboard=[[button]])
            await message.reply(text='Load more', reply_markup=keyboard)


async def search_by_category(category, message):
    result_size = await search_product(message, '', limit=DEFAULT_LIMIT, offset=DEFAULT_OFFSET, category=category.value)
    if result_size == DEFAULT_LIMIT:
        button = types.InlineKeyboardButton(text='⏳',
                                            callback_data=f'category_load_more_'
                                                          f'{DEFAULT_OFFSET}_{category.value}_{message.message_id}')
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[[button]])
        await message.answer(text='Load more', reply_markup=keyboard)


@dp.callback_query(lambda c: c.data and c.data.startswith('category_load_more'))
async def load_more(callback_query: types.CallbackQuery):
    offset = int(callback_query.data.split('_')[-3])
    category = callback_query.data.split('_')[-2]
    message_id = int(callback_query.data.split('_')[-1])

    new_offset = offset + 5
    message = callback_query.message
    result_size = await search_product(message, '', limit=DEFAULT_LIMIT, offset=new_offset, category=category)

    if result_size == DEFAULT_LIMIT:
        button = types.InlineKeyboardButton(text='⏳',
                                            callback_data=f'category_load_more_{new_offset}_{category}_{message_id}')
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[[button]])
        await bot.send_message(chat_id=message.chat.id, reply_to_message_id=message_id, text='Load more',
                               reply_markup=keyboard)


@dp.callback_query(lambda c: c.data and c.data.startswith('load_more'))
async def load_more(callback_query: types.CallbackQuery):
    offset = int(callback_query.data.split('_')[-3])
    value = callback_query.data.split('_')[-2]
    message_id = int(callback_query.data.split('_')[-1])

    new_offset = offset + 5
    message = callback_query.message
    result_size = await search_product(message, value, limit=DEFAULT_LIMIT, offset=new_offset, category=None)

    if result_size == DEFAULT_LIMIT:
        button = types.InlineKeyboardButton(text='⏳',
                                            callback_data=f'load_more_{new_offset}_{value}_{message_id}')
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[[button]])
        await bot.send_message(chat_id=message.chat.id, reply_to_message_id=message_id, text='Load more',
                               reply_markup=keyboard)


if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        tasks = asyncio.gather(main(), asyncio.sleep(1))
        loop.run_until_complete(tasks)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logging.error(f'Error in main: {e}')
