import asyncio
import aiosqlite
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart

TOKEN = os.getenv("TOKEN")
CHANNEL = "@MAONIK_gift"
ADMIN_ID = 7955777831
BOT_USERNAME = "Maonik_bot"

bot = Bot(TOKEN)
dp = Dispatcher()


async def init_db():
    async with aiosqlite.connect("users.db") as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 0,
            ref_id INTEGER,
            ref_bonus INTEGER DEFAULT 0
        )
        """)
        await db.commit()


def menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Баланс", callback_data="balance")],
        [InlineKeyboardButton(text="Бесплатные звёзды", callback_data="free")],
        [InlineKeyboardButton(text="Удвоить звёзды", url="https://t.me/LUDKA_1stars")]
    ])


def back_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад", callback_data="back")]
    ])


def balance_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад", callback_data="back")],
        [InlineKeyboardButton(text="Вывести звёзды", callback_data="withdraw")]
    ])


def withdraw_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="15⭐", callback_data="wd_15"),
            InlineKeyboardButton(text="25⭐", callback_data="wd_25")
        ],
        [
            InlineKeyboardButton(text="50⭐", callback_data="wd_50"),
            InlineKeyboardButton(text="100⭐", callback_data="wd_100")
        ],
        [InlineKeyboardButton(text="Назад", callback_data="balance")]
    ])


async def is_subscribed(user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


@dp.message(CommandStart())
async def start(message: Message):
    user_id = message.from_user.id
    args = message.text.split()
    ref_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else None

    async with aiosqlite.connect("users.db") as db:
        cur = await db.execute("SELECT user_id, ref_id, ref_bonus FROM users WHERE user_id=?", (user_id,))
        user = await cur.fetchone()

        if not user:
            await db.execute(
                "INSERT INTO users (user_id, balance, ref_id, ref_bonus) VALUES (?, 0, ?, 0)",
                (user_id, ref_id)
            )
            await db.commit()

    if not await is_subscribed(user_id):
        await message.answer(
            "‼️Вы не подписаны на канал‼️",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Подписаться", url="https://t.me/MAONIK_gift")]
            ])
        )
        return

    await message.answer("Приветствуем вас в нашем боте!", reply_markup=menu_kb())


@dp.callback_query(F.data == "back")
async def back(call):
    await call.message.edit_text("Приветствуем вас в нашем боте!", reply_markup=menu_kb())


@dp.callback_query(F.data == "balance")
async def balance(call):
    async with aiosqlite.connect("users.db") as db:
        cur = await db.execute("SELECT balance FROM users WHERE user_id=?", (call.from_user.id,))
        bal = (await cur.fetchone())[0]

    await call.message.edit_text(f"Ваш баланс: {bal}⭐", reply_markup=balance_kb())


@dp.callback_query(F.data == "free")
async def free(call):
    link = f"https://t.me/{BOT_USERNAME}?start={call.from_user.id}"

    await call.message.edit_text(
        f"Ваша ссылка:\n{link}",
        reply_markup=back_kb()
    )


@dp.callback_query(F.data == "withdraw")
async def withdraw(call):
    await call.message.edit_text(
        "Выберите сумму:",
        reply_markup=withdraw_kb()
    )


@dp.callback_query(F.data.startswith("wd_"))
async def withdraw_process(call):
    amount = int(call.data.split("_")[1])
    user_id = call.from_user.id
    username = call.from_user.username or f"id{user_id}"

    async with aiosqlite.connect("users.db") as db:
        cur = await db.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        balance = (await cur.fetchone())[0]

        if balance < amount:
            await call.answer("❌ Недостаточно звёзд!", show_alert=True)
            return

        await db.execute(
            "UPDATE users SET balance = balance - ? WHERE user_id=?",
            (amount, user_id)
        )
        await db.commit()

    await bot.send_message(
        ADMIN_ID,
        f"🎁 Вывести {amount} ⭐ пользователю @{username}"
    )

    await call.message.edit_text("✅ Запрос отправлен!")


async def main():
    await init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
