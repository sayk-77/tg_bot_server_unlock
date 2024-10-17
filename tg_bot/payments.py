import asyncio
import logging
import os
import requests
from aiogram import Bot
from dotenv import load_dotenv

from tg_bot.keyboards import create_main_keyboard

load_dotenv()
CRYPTO_TOKEN = os.getenv('CRYPTO_TOKEN')
SERVER_URL = os.getenv('SERVER_URL')


def create_invoice(amount, currency, description='Payment credits'):
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
                    text=f"Replenishment is successful! \nAmount: {amount} {currency}\nTime: {time}",
                )
                response = requests.get(f"{SERVER_URL}CheckCredits", params={"user_id": user_id})
                if response.status_code == 200:
                    result = response.json()
                    await bot.send_message(user_id, text=f"You balance  {result['balance']} credits.", reply_markup=create_main_keyboard())
                await state.clear()
                return
            else:
                await bot.send_message(user_id, text="Error during credit purchase.")
            return
    await bot.send_message(user_id, text="Payment not completed yet. Please wait or try again later.")
