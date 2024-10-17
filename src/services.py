import random
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from tg_bot.bot_instance import bot
from tg_bot.keyboards import destroy_code_keyboard
from database.schemas import GenerateCodeRequest, DestroyCodeRequest, VerificationCodeRequest, UserCreate
from database.models import User
from sqlalchemy.future import select


async def generate_code_service(request: GenerateCodeRequest, db: AsyncSession):
    async with db.begin():
        result = await db.execute(select(User).filter(User.id == request.user_id))
        db_user = result.scalars().first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if db_user.user_code is not None:
        raise HTTPException(status_code=429, detail="Please try again later")

    code = random.randint(10000000, 99999999)
    db_user.user_code = code
    await db.commit()

    await bot.send_message(chat_id=request.user_id, text=f"Your authorization code: {code}",
                           reply_markup=destroy_code_keyboard())

    return {"message": "Code generated and sent to user"}


async def recall_code_service(request: DestroyCodeRequest, db: AsyncSession):
    async with db.begin():
        result = await db.execute(select(User).filter(User.id == request.user_id))
        db_user = result.scalars().first()

    if not db_user or db_user.user_code is None:
        return {"message": "You didn't create the code or it doesn't exist"}

    if db_user.user_code == request.user_code:
        db_user.user_code = None
        await db.commit()
        return {"message": "Your code has been destroyed"}
    else:
        return {"message": "Code destruction error!"}


async def validate_code_service(request: VerificationCodeRequest, db: AsyncSession):
    async with db.begin():
        result = await db.execute(select(User).filter(User.id == request.user_id))
        db_user = result.scalars().first()

    if not db_user or db_user.user_code is None:
        raise HTTPException(status_code=404, detail="User or code not found")

    if db_user.user_code == request.input_code:
        await bot.send_message(chat_id=request.user_id,
                               text=f"You have successfully logged in!\nYour balance is {db_user.balance}")

        return {
            "message": "You have successfully logged in!",
            "user_id": db_user.id,
            "balance": db_user.balance
        }
    else:
        raise HTTPException(status_code=400, detail="Invalid code!")


async def login_service(user: UserCreate, db: AsyncSession):
    async with db.begin():
        result = await db.execute(select(User).filter(User.id == user.id))
        db_user = result.scalars().first()

    if db_user:
        return {"message": f"User {user.id} already registered.", "balance": db_user.balance}

    try:
        new_user = User(id=user.id)
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return {"message": f"User {user.id} registered successfully.", "balance": new_user.balance}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


async def get_credit_info_service(user_id: int, db: AsyncSession):
    async with db.begin():
        result = await db.execute(select(User).filter(User.id == user_id))
        db_user = result.scalars().first()

    if db_user:
        return {"balance": db_user.balance}
    else:
        raise HTTPException(status_code=404, detail="User not found")


async def buy_credits_service(user_id: int, amount: float, db: AsyncSession):
    async with db.begin():
        result = await db.execute(select(User).filter(User.id == user_id))
        db_user = result.scalars().first()

    if db_user:
        db_user.balance += amount
        await db.commit()
        return {"message": f"Balance updated by {amount} credits."}
    else:
        raise HTTPException(status_code=404, detail="User not found")


async def is_admin_service(user_id: int, db: AsyncSession):
    async with db.begin():
        result = await db.execute(select(User).filter(User.id == user_id))
        db_user = result.scalars().first()

    if db_user:
        return {"is_admin": db_user.account_type == "admin"}
    else:
        raise HTTPException(status_code=404, detail="User not found")


async def get_all_users_service(db: AsyncSession):
    async with db.begin():
        result = await db.execute(select(User))
        users = result.scalars().all()
    return [{"id": user.id, "balance": user.balance} for user in users]