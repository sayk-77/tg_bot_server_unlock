from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def payment_stars(amount: int):
    builder = InlineKeyboardBuilder()
    builder.button(text=f"To pay {amount} ⭐️", pay=True)

    return builder.as_markup()


def payment_card(amount: int):
    builder = InlineKeyboardBuilder()
    builder.button(text=f"To pay {amount} RUB", pay=True)

    return builder.as_markup()


def currency_keyboard(amount: int) -> InlineKeyboardMarkup:
    button = [
        [InlineKeyboardButton(text="🟣 YooMoney", callback_data=f"button_bank_card")],
        [InlineKeyboardButton(text="⭐️ Telegram Stars", callback_data=f"button_stars")],
        [InlineKeyboardButton(text="💵 CryptoBot (USDT)", callback_data="button_usdt")],
        [InlineKeyboardButton(text="💵 CryptoBot (TON)", callback_data=f"button_ton")],
        [InlineKeyboardButton(text="💵 CryptoBot (ETH)", callback_data=f"button_eth")]
    ]

    return InlineKeyboardMarkup(inline_keyboard=button)


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


def destroy_code_keyboard() -> InlineKeyboardMarkup:
    button = [
        InlineKeyboardButton(text="Destroy the code", callback_data="button_cancel"),
    ]

    return InlineKeyboardMarkup(inline_keyboard=[button])
