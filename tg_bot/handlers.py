import os

import requests
from aiogram import Dispatcher, types, Bot, F
from aiogram.enums import ContentType
from aiogram.filters import CommandStart
from aiogram.types import LabeledPrice
from aiogram.fsm.context import FSMContext

from tg_bot.bot_instance import bot
from tg_bot.keyboards import create_main_keyboard, currency_keyboard, create_credit_purchase_keyboard, payment_stars, \
    payment_card
from tg_bot.states import UserState
from tg_bot.payments import check_payment_status, create_invoice
from dotenv import load_dotenv

from tg_bot.utils import currency_rates, stars_course, get_user_code, is_user_admin

load_dotenv()
SERVER_URL = os.getenv('SERVER_URL')
YOU_MONEY_API = os.getenv('YOU_MONEY_API')


async def hello_message(message: types.Message) -> None:
    user_id = message.from_user.id
    response = requests.post(f"{SERVER_URL}Login", json={"id": user_id})

    if response.status_code == 200:
        is_admin = await is_user_admin(user_id)
        await message.answer(f"Hello, {message.from_user.full_name}! Your id {user_id}",
                             reply_markup=create_main_keyboard(is_admin))
    else:
        await message.answer("Error during registration.")


async def handle_message(message: types.Message, state: FSMContext) -> None:
    user_id = message.from_user.id

    if message.text == "Buy Credits":
        await message.answer("How many credits do you want to buy?", reply_markup=create_credit_purchase_keyboard())
        await state.set_state(UserState.WAITING_FOR_AMOUNT)
        return

    if await state.get_state() == UserState.WAITING_FOR_AMOUNT.state:
        try:
            amount = float(message.text)
            if amount <= 0:
                raise ValueError

            await state.update_data(amount=amount)

            await message.answer("Payment methods", reply_markup=currency_keyboard(amount=message.text))

        except ValueError as e:
            if message.text == "Cancel":
                await state.clear()
                await message.answer("Operation canceled.", reply_markup=create_main_keyboard())
                return
            print(e)
            await message.answer("Please enter a valid amount.")
        return

    if message.text == "Credit Info":
        response = requests.get(f"{SERVER_URL}CheckCredits", params={"user_id": user_id})
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


async def handle_currency_selection(callback_query: types.CallbackQuery, state: FSMContext, bot: Bot):
    user_id = callback_query.from_user.id

    state_data = await state.get_data()
    amount = state_data.get('amount')
    global currency
    await state.update_data(currency="USDT")

    await state.update_data(message_id=callback_query.message.message_id)

    if callback_query.data == "button_cancel":
        user_id = callback_query.from_user.id
        user_code = await get_user_code(user_id)

        response = requests.post(f"{SERVER_URL}DestroyCode", json={"user_id": user_id, "user_code": user_code}).json()
        print(response)
        await bot.edit_message_text(text=response['message'], chat_id=user_id,
                                    message_id=callback_query.message.message_id)
        return

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
            reply_markup=payment_stars(to_be_paid)
        )
        await bot.delete_message(chat_id=user_id, message_id=callback_query.message.message_id)
        await state.set_state(UserState.WAITING_FOR_PAYMENT)
        return

    if callback_query.data == "button_bank_card":
        to_be_paid = amount * 10000
        prices = [LabeledPrice(label=f"{amount} Credits", amount=to_be_paid)]
        await callback_query.message.answer_invoice(
            title="Purchase Credits",
            description=f"Purchase {amount} credits!",
            prices=prices,
            provider_token=YOU_MONEY_API,
            payload="credit_purchase",
            currency="RUB",
            reply_markup=payment_card(amount * 100)
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


async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


async def process_successful_payment(message: types.Message):
    payment_info = message.successful_payment

    currency_message = payment_info.currency
    total_amount = payment_info.total_amount / 100
    invoice_payload = payment_info.invoice_payload

    await message.answer(f"Thanks for the purchase! The payment for the amount of {total_amount} {currency_message} was successful.")


def register_handlers(dp: Dispatcher):
    dp.message.register(hello_message, CommandStart())
    dp.message.register(handle_message)
    dp.message.register(process_successful_payment, F.successful_payment)
    dp.pre_checkout_query.register(process_pre_checkout_query)
    dp.callback_query.register(handle_currency_selection)
