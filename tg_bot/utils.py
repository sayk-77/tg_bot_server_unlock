import os
from typing import Any

import requests
from sqlalchemy.future import select
from database.database import get_db
from database.models import User
from dotenv import load_dotenv

load_dotenv()
SERVER_URL = os.getenv('SERVER_URL')

currency_rates = {
    "USDT": 1.0,
    "TON": 0.2,
    "ETH": 0.00038
}

stars_course = 50


async def get_user_code(user_id: int):
    async for db in get_db():
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalars().first()
        if user:
            return user.user_code
        return None


async def check_user(user_id: int) -> Any | None:
    async for db in get_db():
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalars().first()
        if user:
            return user.name
        else:
            await create_user(user_id)
            return
    return None


async def create_user(user_id: int) -> bool:
    async for db in get_db():
        new_user = User(
            id=user_id
        )
        db.add(new_user)
        await db.commit()
        return True


async def set_user_name(user_id: int, name: str) -> str | bool:
    async for db in get_db():
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalars().first()
        if user:
            user.name = name
            await db.commit()
            return True
    return False


async def add_credit_user(user_id: int, amount: int) -> int | None:
    async for db in get_db():
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalars().first()
        if user:
            user.balance += amount
            await db.commit()
            return user.balance
    return None


async def delete_code_user(user_id: str) -> str:
    async for db in get_db():
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalars().first()
        if user:
            user.user_code = None
            await db.commit()
            return "Your code has been destroyed!"
    return "Code destruction error!"


async def get_user_balance(user_id: int):
    async for db in get_db():
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalars().first()
        if user:
            return user.balance
        return None


async def is_user_admin(user_id: int):
    response = requests.get(f"{SERVER_URL}IsAdmin", params={"user_id": user_id})
    return response.json().get("is_admin", False)
