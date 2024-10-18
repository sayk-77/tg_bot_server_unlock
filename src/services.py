import random

from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from tg_bot.bot_instance import bot
from tg_bot.keyboards import destroy_code_keyboard
from database.models import User
from sqlalchemy.future import select


async def generate_code_service(account: str, db: AsyncSession):
    async with db.begin():
        result = await db.execute(select(User).filter(or_(User.id == account, User.name == account)))
        db_user = result.scalars().first()

        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        if db_user.user_code is not None:
            raise HTTPException(status_code=429, detail="Please try again later")

        code = random.randint(10000000, 99999999)
        db_user.user_code = code
        await db.commit()

        await bot.send_message(chat_id=db_user.id, text=f"Your authorization code: {code}",
                               reply_markup=destroy_code_keyboard())

        return {"message": "Code generated and sent to user"}


async def recall_code_service(account: str, code: int, db: AsyncSession):
    async with db.begin():
        result = await db.execute(select(User).filter(or_(User.id == account, User.name == account)))
        db_user = result.scalars().first()

        if not db_user or db_user.user_code is None:
            return {"message": "You didn't create the code or it doesn't exist"}

        if db_user.user_code == code:
            db_user.user_code = None
            await db.commit()
            return {"message": "Your code has been destroyed"}
        else:
            return {"message": "Code destruction error!"}


async def get_credit_info_service(account: str, code: int, db: AsyncSession):
    async with db.begin():
        result = await db.execute(select(User).filter(or_(User.id == account, User.name == account)))
        db_user = result.scalars().first()

        if db_user:
            if db_user.user_code == code:
                return {"balance": db_user.balance}
            else:
                raise HTTPException(status_code=400, detail="Invalid code")
        else:
            raise HTTPException(status_code=404, detail="User not found")
