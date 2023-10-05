import asyncio
import datetime

from tgmedbot.db.connection import SqliteConnection
import aiogram


from tgmedbot.schemas import BotConfigModel
# from handlers import general
from tgmedbot.handlers import basic, fsm_handlers
from tgmedbot.constants.common import CREDENTIALS_DIR_PATH
from tgmedbot.utils import load_config, warningColorstr, async_time_counter

from tgmedbot.db.actions import delete_inactive_users


@async_time_counter()
async def delete_inactive_users_on_schedule() -> int:
    # for debug use 1.0
    every_period: float = 60 * 60

    max_deletions: int = 0
    performed_deletions: int = 0
    # use `-1` only for debugging since anything will be less than future
    days_diff: int = 10

    while True:
        async with SqliteConnection.lock:
            # Delete inactive users from the database here
            async with SqliteConnection.get_session() as session:
                # Calculate the cutoff time
                cutoff_time = datetime.datetime.utcnow() - datetime.timedelta(days=days_diff)

                deleted_users: int = await delete_inactive_users(session, cutoff_time)

        print(warningColorstr(f"Deleted {deleted_users} users at {datetime.datetime.now().strftime('%H:%M:%S.%f')}"))
        performed_deletions += 1
        # Log the number of deleted users
        print(warningColorstr(f"Total deletions so far: {performed_deletions}"))

        # Check if we have reached the max deletions limit
        if max_deletions != -1 and performed_deletions >= max_deletions:
            print(warningColorstr((f"Breaking the infinite loop for deleting inactive users "
                                   f"with performed deletions={performed_deletions}")))
            break

        await asyncio.sleep(every_period)  # Sleep for 60 minutes

    return 200


async def main() -> None:
    bot_config_path = CREDENTIALS_DIR_PATH / 'bot.yaml'
    if bot_config_path.exists() is False:
        raise FileNotFoundError(f"Before running the bot you have to create `bot.yaml` at {CREDENTIALS_DIR_PATH}")

    BotConfig = BotConfigModel(**load_config(bot_config_path))
    bot: aiogram.Bot = aiogram.Bot(token=BotConfig.token)
    dispatcher = aiogram.Dispatcher()

    # routers:
    dispatcher.include_router(fsm_handlers.router)
    dispatcher.include_router(basic.router)

    # remove extra updates + start polling:
    await bot.delete_webhook(drop_pending_updates=True)
    # create tasks:
    delete_inactive_task: asyncio.Task = asyncio.create_task(delete_inactive_users_on_schedule())
    polling: asyncio.Task = asyncio.create_task(dispatcher.start_polling(bot))

    # now await them:
    await delete_inactive_task
    await polling  # dispatcher.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
