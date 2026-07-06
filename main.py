import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandStart
from aiogram.types.bot_command import BotCommand
from aiogram.types import Message
from dotenv import load_dotenv

import time

import random
import sqlite3

from aiogram.utils.text_decorations import markdown_decoration

from aiogram.enums import ParseMode

# load data from .env (TOKEN rn)
load_dotenv()

# INIT sqlite data base
con = sqlite3.connect("pears.db")
cur = con.cursor()

cur.execute(
    """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, 
            username TEXT,
            pears_amount INTEGER DEFAULT 10,
            last_date TEXT
        )
    """
)
con.commit()
con.close()



TOKEN = os.getenv("TOKEN")

_cd : str | None = os.getenv("COOLDOWN")

if _cd is None:
    print("Specify cooldown in .env file!")
    exit(1)

COOLDOWN = int(_cd)

dp = Dispatcher()

# to make an good word for bot to use
def pluralize(number : int | float, one:str, mult:str):
    return one if abs(number) == 1 else mult

# load leaders from DB
def getLeaders():
    con = sqlite3.connect("pears.db")
    cur = con.cursor()

    cur.execute(
        "SELECT username, pears_amount FROM users ORDER BY pears_amount DESC LIMIT 10",
    )
    result = cur.fetchall()

    con.close()

    return result


# load user data from sql database
def loadUserData(id:int):
    con = sqlite3.connect("pears.db")
    cur = con.cursor()

    cur.execute(
        "SELECT username, pears_amount, last_date FROM users WHERE user_id = ?",
        (id,),
    )

    result = cur.fetchone()

    con.close()

    return result

# write user data to sql database
def writeData(id : int, data : tuple[str, int, float]):

    username : str = data[0]
    pears_amount : int = data[1]
    today_date : float = data[2]

    con = sqlite3.connect("pears.db")
    cur = con.cursor()

    cur.execute(
        """
        INSERT OR REPLACE INTO users (user_id, username, pears_amount, last_date)
        VALUES (?, ?, ?, ?)
        """,
        (id, username, pears_amount, today_date),
    )

    con.commit()
    con.close()

# main code for growing
@dp.message(CommandStart())
async def getPears(msg: Message):
    userId : int | None = msg.from_user and msg.from_user.id

    if userId is None:
        return

    info = loadUserData(userId)

    currentTime = time.time()

    username : str | None = msg.from_user.first_name if msg.from_user else None

    if username is None:
        return
    
    if info is not None:

        pears_amount : int = info[1]
        last_time : int = info[2]

        laststamp = float(last_time)

        seconds_passed = currentTime - laststamp

        if seconds_passed < COOLDOWN: #if user has active cooldown
            mins : float = seconds_passed // 60
            text : str = pluralize(mins, " minute", " minutes")
            timeOutInfo : str = f"{int(mins)}{text} ago"

            if int(mins) == 0:
                timeOutInfo = "right now"

            seconds_left : int = int(COOLDOWN - seconds_passed)
            left_mins : float = seconds_left // 60
            left_secs : float = seconds_left % 60

            left_min_word : str = pluralize(left_mins, "minute", "minutes")
            left_sec_word : str = pluralize(left_secs, "second", "seconds")

            if left_mins > 0:
                timeLeft = f"{left_mins} {left_min_word} {left_secs} {left_sec_word}"
            else:
                timeLeft = f"{left_secs} {left_sec_word}"

            await msg.answer(
                text=f"you gained your pears {timeOutInfo}! ⏳\n"
                f"come back after {timeLeft}!\n\n"
                f"pears amount: {pears_amount}"
            )
            return
    else:
        pears_amount = 10
    

    change = random.randint(-10, 10)

    pears_amount = pears_amount + change

    if change > 0:
        await msg.answer(
            text=f"you got {abs(change)} pears!\n" 
            f"pears amount: {pears_amount}"
        )

    if change < 0:
        if pears_amount < 0:
            pears_amount = 0
            await msg.answer(text=f"you lost all of your pears :(")
            
        else:
            await msg.answer(
                text=f"you lost {abs(change)} pears :( \n" 
                f"pears amount: {pears_amount}"
            )

    if change == 0:
        await msg.answer(
            text=f"you did not get any pears :( \n" 
            f"pears amount: {pears_amount}"
        )

    
    writeData(userId, (username, pears_amount, currentTime))

@dp.message(Command("leaders"))
async def leaders(msg : Message):
    leaders = getLeaders()

    if len(leaders) == 0:
        await msg.answer(text="There is no data in the DataBase! No one played!")
        return

    top_text = "🏆 THE MOST PEARS LEADERBOARD 🏆\n\n"

    for index, player in enumerate(leaders, start=1):
        username, amount = player[0], player[1]

        if index == 1:
            medal = "🥇"
        elif index == 2:
            medal = "🥈"
        elif index == 3:
            medal = "🥉"
        else:
            medal = f" {index}" 

        safe_username : str = markdown_decoration.quote(str(username))
        safe_amount : str = markdown_decoration.quote(str(amount))

        top_text += f"{medal} {safe_username} — {safe_amount} pears \n"

    if msg:
        await msg.answer(text=top_text, parse_mode=ParseMode.MARKDOWN_V2)

    



# run the bot
async def main():

    token : str | None = TOKEN

    if token is None:
        print("Please specify token in .env file!")
        exit(1)

    bot = Bot(token=token)

    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Try to get your pears"),
            BotCommand(command="leaders", description="Get the leaders leaderboard"),
        ]
    )

    await dp.start_polling(bot) # type: ignore


if __name__ == "__main__":
    asyncio.run(main())