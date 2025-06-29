import os
import state_num
import asyncio
import logging
from aiogram import Bot, Dispatcher

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.handlers import client




from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO,
                    )


async def reset_var():

    state_num.number = 0
    print("Переменная обнулена в 00:00!")

async def main():

    bot = Bot(token=os.getenv('TG_TOKEN'))
    dp = Dispatcher()
    scheduler = AsyncIOScheduler()
    scheduler.add_job(reset_var, 'cron', hour=0, minute=0)
    scheduler.start()

    dp.include_router(client)
    dp.startup.register(startup)
    dp.shutdown.register(shutdown)
    await dp.start_polling(bot)


async def startup(dispatcher: Dispatcher):
    #await async_main()
    logging.info('Bot started up...')


async def shutdown(dispatcher: Dispatcher):
    logging.info('Bot is shutting down...')


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info('Bot stopped')