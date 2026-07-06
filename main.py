import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandStart
from aiogram.types.bot_command import BotCommand
from aiogram.types import Message
from dotenv import load_dotenv

from typing import NamedTuple

import time

import random
import sqlite3

from aiogram.utils.text_decorations import markdown_decoration

from aiogram.enums import ParseMode

import json

# load data from .env
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
            last_date TEXT,
            language TEXT DEFAULT 'en'
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

# locales loading
def load_locales() -> dict[str, dict[str, str]]:
    locales: dict[str, dict[str, str]] = {}
    for lang in ["en", "ru"]:
        with open(f"locales/{lang}.json", "r", encoding="utf-8") as f:
            locales[lang] = json.load(f)
    return locales

LOCALIZATION = load_locales()

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

class UserData(NamedTuple):
    username: str
    pears_amount: int
    last_date: float
    language: str


# load user data from sql database
def loadUserData(id: int) -> UserData | None:
    con = sqlite3.connect("pears.db")
    cur = con.cursor()

    cur.execute(
        "SELECT username, pears_amount, last_date, language FROM users WHERE user_id = ?",
        (id,),
    )
    result = cur.fetchone()
    con.close()
    

    if result is None:
        return
    
    return UserData(
        result[0], result[1], result[2], result[3]
    )


# write user data to sql database
def writeData(id: int, data: tuple[str, int, float, str]):

    username: str = data[0]
    pears_amount: int = data[1]
    today_date: float = data[2]
    lang: str = data[3]

    con = sqlite3.connect("pears.db")
    cur = con.cursor()

    cur.execute(
        """
        INSERT OR REPLACE INTO users (user_id, username, pears_amount, last_date, language)
        VALUES (?, ?, ?, ?, ?)
        """,
        (id, username, pears_amount, today_date, lang),
    )

    con.commit()
    con.close()

# main code for growing
@dp.message(CommandStart())
async def getPears(msg: Message):
    userId: int | None = msg.from_user.id if msg.from_user else None
    if userId is None:
        return

    info = loadUserData(userId)
    currentTime = time.time()
    username: str | None = msg.from_user.first_name if msg.from_user else None

    if username is None:
        return
    
    lang: str = "en"
    pears_amount: int = 10

    if info is not None:
        pears_amount = int(info[1])
        last_time: float = float(info[2])
        lang = str(info[3])

        seconds_passed = currentTime - last_time

        if seconds_passed < COOLDOWN: 
            mins: float = seconds_passed // 60
            
            word_min = LOCALIZATION[lang]["minute"] if int(mins) == 1 else LOCALIZATION[lang]["minutes"]
            
            if int(mins) == 0:
                timeOutInfo = LOCALIZATION[lang]["time_now"]
            else:
                timeOutInfo = LOCALIZATION[lang]["time_ago"].format(int_mins=int(mins), word_min=word_min)

            seconds_left: int = int(COOLDOWN - seconds_passed)
            left_mins: float = seconds_left // 60
            left_secs: float = seconds_left % 60

            left_min_word = LOCALIZATION[lang]["minute"] if left_mins == 1 else LOCALIZATION[lang]["minutes"]
            left_sec_word = LOCALIZATION[lang]["second"] if left_secs == 1 else LOCALIZATION[lang]["seconds"]

            if left_mins > 0:
                timeLeft = f"{left_mins} {left_min_word} {left_secs} {left_sec_word}"
            else:
                timeLeft = f"{left_secs} {left_sec_word}"

            await msg.answer(
                text=LOCALIZATION[lang]["cooldown"].format(
                    time_info=timeOutInfo, time_left=timeLeft, amount=pears_amount
                )
            )
            return

    change = random.randint(-10, 10)
    pears_amount = pears_amount + change

    if change > 0:
        await msg.answer(text=LOCALIZATION[lang]["got_pears"].format(change=abs(change), amount=pears_amount))
    elif change < 0:
        if pears_amount < 0:
            pears_amount = 0
            await msg.answer(text=LOCALIZATION[lang]["lost_all"])
        else:
            await msg.answer(text=LOCALIZATION[lang]["lost_pears"].format(change=abs(change), amount=pears_amount))
    else:
        await msg.answer(text=LOCALIZATION[lang]["no_change"].format(amount=pears_amount))
    
    writeData(userId, (username, pears_amount, currentTime, lang))

@dp.message(Command("leaders"))
async def leaders(msg: Message):
    userId: int | None = msg.from_user.id if msg.from_user else None
    if userId is None:
        return

    info = loadUserData(userId)
    lang = str(info[3]) if info is not None else "en"

    leaders_list = getLeaders()

    if len(leaders_list) == 0:
        await msg.answer(text=LOCALIZATION[lang]["no_data"])
        return

    top_text = LOCALIZATION[lang]["leaderboard_title"]

    for index, player in enumerate(leaders_list, start=1):
        username, amount = player[0], player[1]

        medal = "🥇" if index == 1 else "🥈" if index == 2 else "🥉" if index == 3 else f" {index}"

        safe_username: str = markdown_decoration.quote(str(username))
        safe_amount: str = markdown_decoration.quote(str(amount))

        top_text += LOCALIZATION[lang]["leaderboard_line"].format(
            medal=medal, username=safe_username, amount=safe_amount
        )

    await msg.answer(text=top_text, parse_mode=ParseMode.HTML)

@dp.message(Command("lang"))
async def change_lang(msg: Message):
    userId: int | None = msg.from_user.id if msg.from_user else None
    if userId is None or msg.text is None:
        return

    args = msg.text.split()
    if len(args) < 2 or args[1].lower() not in ["ru", "en"]:
        await msg.answer("Usage: `/lang en` or `/lang ru` 🌐")
        return

    new_lang = args[1].lower()
    info = loadUserData(userId)

    if info is not None:
        username, pears_amount, last_time = info[0], int(info[1]), float(info[2])
    else:
        username = msg.from_user.first_name if msg.from_user else "User"
        pears_amount = 10
        last_time = 0.0

    writeData(userId, (username, pears_amount, last_time, new_lang))
    await msg.answer(text=LOCALIZATION[new_lang]["lang_changed"], parse_mode=ParseMode.HTML)



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
            BotCommand(command="lang", description="Change language / Сменить язык"),
        ]
    )

    await dp.start_polling(bot) # type: ignore


if __name__ == "__main__":
    asyncio.run(main())