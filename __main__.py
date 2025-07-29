import asyncio
from .bot import BotModular

def main():
    asyncio.run(run_bot())

async def run_bot():
    bot = BotModular()
    await bot.conectar()
    await bot.set_account()
    await bot.trading_loop()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(main())
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\nClosing the program.")
    finally:
        loop.close()
    
