import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN, ENV
from handlers import start, children, tasks, stats, payments

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    start.register_handlers(dp)
    children.register_handlers(dp)
    tasks.register_handlers(dp)
    stats.register_handlers(dp)
    payments.register_handlers(dp)

    logger.info(f"🎄 Starting Advent Bot RU in ENV={ENV}")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
