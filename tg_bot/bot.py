import asyncio
import logging
import requests
from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
import os
load_dotenv()

CRYPTO_TOKEN = os.getenv('CRYPTO_TOKEN')
TOKEN = os.getenv('TOKEN')
SERVER_URL = os.getenv('SERVER_URL')

storage = MemoryStorage()
dp = Dispatcher()

stars_course = 50

class UserState(StatesGroup):
    WAITING_FOR_AMOUNT = State()
    WAITING_FOR_PAYMENT = State()
    WAITING_FOR_AMOUNT_XTR = State()

async def is_user_admin(user_id):
    response = requests.get(f"{SERVER_URL}IsAdmin", params={"user_id": user_id})
    return response.json().get("is_admin", False)

def create_main_keyboard(is_admin=False) -> ReplyKeyboardMarkup:
    if is_admin:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="View All Users")],
                [KeyboardButton(text="View User by ID")]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    else:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Buy Credits"), KeyboardButton(text="Credit Info")]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )

    return keyboard

def create_credit_purchase_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Cancel")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard


def payment_keyboard(amount: int):
    builder = InlineKeyboardBuilder()
    builder.button(text=f"To pay {amount} ⭐️", pay=True)

    return builder.as_markup()

def currency_keyboard(amount: int) -> InlineKeyboardMarkup:
    button = [
        InlineKeyboardButton(text="USDT", callback_data="button_usdt"),
        InlineKeyboardButton(text="TON", callback_data=f"button_ton"),
        InlineKeyboardButton(text="ETH", callback_data=f"button_eth"),
        InlineKeyboardButton(text="TG STARS", callback_data=f"button_stars")
    ]

    return InlineKeyboardMarkup(inline_keyboard=[button])

currency_rates = {
    "USDT": 1.0,
    "TON": 0.2,
    "ETH": 0.00038,
}

def create_invoice(amount, currency, description='Оплата кредита'):
    url = 'https://testnet-pay.crypt.bot/api/createInvoice'
    headers = {
        'Crypto-Pay-API-Token': CRYPTO_TOKEN
    }
    data = {
        'amount': amount,
        'currency': currency,
        'description': description,
        'asset': currency
    }
    response = requests.post(url, json=data, headers=headers).json()

    if response['ok']:
        return response['result']['pay_url'], response['result']['invoice_id']
    else:
        logging.error(f"Error creating invoice: {response}")
        return None, None

def check_invoice_status(invoice_id):
    url = 'https://testnet-pay.crypt.bot/api/getInvoices'
    headers = {
        'Crypto-Pay-API-Token': CRYPTO_TOKEN
    }
    params = {
        'invoice_ids': [invoice_id]
    }

    response = requests.get(url, params=params, headers=headers).json()

    if response['ok']:
        if 'result' in response and 'items' in response['result'] and response['result']['items']:
            invoice_info = response['result']['items'][0]
            status = invoice_info['status']
            time = invoice_info['created_at']
            return status, time
        else:
            print("Error: No items found in the API response.")
            return None
    else:
        print("Error: API response indicates failure.")
        return None


@dp.callback_query(lambda c: c.data)
async def handle_currency_selection(callback_query: types.CallbackQuery, state: FSMContext, bot: Bot):
    user_id = callback_query.from_user.id

    state_data = await state.get_data()
    amount = state_data.get('amount')
    global currency
    await state.update_data(currency="USDT")

    await state.update_data(message_id=callback_query.message.message_id)

    if callback_query.data == "button_usdt":
        currency = "USDT"
    if callback_query.data == "button_ton":
        currency = "TON"
    if callback_query.data == "button_eth":
        currency = "ETH"

    if callback_query.data == "button_stars":
        to_be_paid = amount * stars_course

        prices = [LabeledPrice(label=f"{amount} Credits", amount=to_be_paid)]
        await callback_query.message.answer_invoice(
            title="Purchase Credits",
            description=f"Purchase {amount} credits!",
            prices=prices,
            provider_token="",
            payload="credit_purchase",
            currency="XTR",
            reply_markup=payment_keyboard(to_be_paid)
        )
        await bot.delete_message(chat_id=user_id, message_id=callback_query.message.message_id)
        await state.set_state(UserState.WAITING_FOR_PAYMENT)
        return

    pay_url, invoice_id = create_invoice(currency_rates[currency] * amount, currency=currency)

    if pay_url:
        await callback_query.message.edit_text(pay_url)
        await state.update_data(invoice_id=invoice_id, amount=amount)
        await state.set_state(UserState.WAITING_FOR_PAYMENT)

        await check_payment_status(bot, invoice_id, amount, user_id, state)
    else:
        await callback_query.message.edit_text("Error creating invoice.")



@dp.message(CommandStart())
async def hello_message(message: types.Message) -> None:
    user_id = message.from_user.id
    response = requests.post(f"{SERVER_URL}Login", json={"id": user_id})

    if response.status_code == 200:
        result = response.json()
        is_admin = await is_user_admin(user_id)
        await message.answer(f"Hello, {message.from_user.full_name}! Your id {user_id}",
                             reply_markup=create_main_keyboard(is_admin))
    else:
        await message.answer("Error during registration.")

@dp.message()
async def handle_message(message: types.Message, state: FSMContext, bot: Bot) -> None:
    user_id = message.from_user.id

    if message.text == "Buy Credits":
        await message.answer("How many credits do you want to buy?", reply_markup=create_credit_purchase_keyboard())
        await state.set_state(UserState.WAITING_FOR_AMOUNT)
        return

    if await state.get_state() == UserState.WAITING_FOR_AMOUNT.state:
        try:
            amount = int(message.text)
            if amount <= 0:
                raise ValueError

            await state.update_data(amount=amount)

            await message.answer("Choose the appropriate currency", reply_markup=currency_keyboard(amount=message.text))

        except ValueError:
            if message.text == "Cancel":
                await state.clear()
                await message.answer("Operation canceled.", reply_markup=create_main_keyboard())
                return
            await message.answer("Please enter a valid amount.")
        return

    if message.text == "Credit Info":
        response = requests.get(f"{SERVER_URL}CreditInfo", params={"user_id": user_id})
        if response.status_code == 200:
            result = response.json()
            await message.answer(f"You have {result['balance']} credits.")
        else:
            await message.answer("Error fetching credit information.")

    if message.text == "View All Users":
        response = requests.get(f"{SERVER_URL}AllUsers")
        if response.status_code == 200:
            users = response.json()
            users_info = "\n".join([f"ID: {user['id']}, Balance: {user['balance']}" for user in users])
            await message.answer(f"Users:\n{users_info}")
        else:
            await message.answer("Error fetching users.")

    if message.text == "Cancel":
        await state.clear()
        await message.answer("Operation canceled.", reply_markup=create_main_keyboard())

async def check_payment_status(bot: Bot, invoice_id, amount, user_id, state):
    for _ in range(10):
        await asyncio.sleep(10)
        status, time = check_invoice_status(invoice_id)
        state_data = await state.get_data()
        message_id = state_data.get('message_id')
        currency = state_data.get('currency')

        if status == 'paid':
            response = requests.post(f"{SERVER_URL}BuyCredits", params={"user_id": user_id, "amount": amount})
            if response.status_code == 200:
                await bot.edit_message_text(
                    chat_id=user_id,
                    message_id=message_id,
                    text=f"Пополнение успешно! \nСумма: {amount} {currency}\nВремя: {time}"
                )
                response = requests.get(f"{SERVER_URL}CreditInfo", params={"user_id": user_id})
                if response.status_code == 200:
                    result = response.json()
                    await bot.send_message(user_id, text=f"You balance  {result['balance']} credits.", reply_markup=create_main_keyboard())
                await state.clear()
                return
            else:
                await bot.send_message(user_id, text="Error during credit purchase.")
            return
    await bot.send_message(user_id, text="Payment not completed yet. Please wait or try again later.")

async def main() -> None:
    bot = Bot(TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())