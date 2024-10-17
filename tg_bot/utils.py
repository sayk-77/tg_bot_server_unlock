import os
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


async def is_user_admin(user_id: int):
    response = requests.get(f"{SERVER_URL}IsAdmin", params={"user_id": user_id})
    return response.json().get("is_admin", False)
