# 🍐 Pears Growing Telegram Bot

An asynchronous Telegram bot built with **Aiogram 3** where users can test their luck, grow (or lose) pears, compete in a global leaderboard, and track active cooldowns.

The project has been fully refactored to support **Strict Type-Checking**, ensuring runtime stability and eliminating any hidden `NoneType` attribute errors.

---

## ✨ Features

* **Strict Typing:** The codebase is fully compliant with strict type-checking tools (Pyright/Pylance in `strict` mode). All potential `None` leaks are handled using defensive type guards.
* **Core Gameplay:** Every $X$ minutes (configured via environment variables), users can trigger the `/start` command to randomly gain or lose pears (ranging from -10 to +10).
* **Smart Cooldowns:** The bot dynamically calculates the remaining time before the next attempt, featuring clean plurals formatting (*1 minute* vs *5 minutes*).
* **Global Leaderboard:** The `/leaders` command displays the top 10 players, with automatic username escaping to guarantee safe parsing via `MarkdownV2`.
* **Local Storage:** Lightweight database integration out of the box using built-in `sqlite3`.

---

## 🛠️ Tech Stack

* **Language:** Python 3.11+
* **Framework:** Aiogram 3.x (Asyncio)
* **Database:** SQLite3
* **Type Checker:** Pyright / Pylance (`strict` mode)
* **Environment:** Python-dotenv

---

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone [https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git)
cd YOUR_REPO_NAME

```

### 2. Configure Environment Variables

Create a `.env` file in the root directory of the project and specify your configuration parameters:

```env
TOKEN=your_telegram_bot_token_here
COOLDOWN=3600  # Cooldown time in seconds (e.g., 3600 seconds = 1 hour)

```

### 3. Install Dependencies

Install the required asynchronous framework and the environment variable helper:

```bash
pip install aiogram python-dotenv

```

### 4. Run the Bot

```bash
python main.py

```

---

## 📋 Bot Commands

* `/start` — Try your luck to grow new pears or lose your current ones. New users are automatically registered with a starter balance of 10 pears.
* `/leaders` — Check the global leaderboard displaying the top 10 players with the most pears.
* `/lang (en/ru)` – Change the language for the bot (by default English)

---

## 🔒 Type Safety Overview

This version of the bot focuses heavily on type safety best practices:

* All incoming contexts from `msg.from_user` are validated immediately upon arrival.
* User data fetched from the SQLite database is strictly cast to its expected primitives (`int`, `float`, `str`) before processing any business logic.
* The leaderboard uses `aiogram.utils.text_decorations.markdown_decoration` to fully escape reserved characters in Telegram usernames, completely eliminating `TelegramBadRequest` layout parsing exceptions.
