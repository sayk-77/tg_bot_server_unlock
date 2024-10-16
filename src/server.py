import os
import random
import time

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from database import init_db, SessionLocal
from models import User
from schemas import UserCreate, GenerateCodeRequest, VerificationCodeRequest
from aiogram import Bot
from dotenv import load_dotenv

load_dotenv()
codes = {}


app = FastAPI()
bot = Bot(os.getenv("TOKEN"))


@app.on_event("startup")
async def startup_event():
    init_db()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/Api/RequestCode")
async def generate_code(request: GenerateCodeRequest, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == request.user_id).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    current_time = time.time()

    if request.user_id in codes:
        last_request_time, _ = codes[request.user_id]
        if current_time - last_request_time <= 30:
            raise HTTPException(status_code=429, detail="Please try again later")

    code = random.randint(10000000, 99999999)
    codes[request.user_id] = (current_time, code)

    await bot.send_message(chat_id=request.user_id, text=f"Your authorization code: {code}")


@app.post("/Api/ValidateCode")
async def validate_code(request: VerificationCodeRequest, db: Session = Depends(get_db)):
    stored_code_data = codes.get(request.user_id)

    if stored_code_data is None:
        raise HTTPException(status_code=404, detail="User or code not found")

    _, stored_code = stored_code_data

    print(request.input_code, stored_code)

    if stored_code == request.input_code:
        db_user = db.query(User).filter(User.id == request.user_id).first()

        await bot.send_message(chat_id=request.user_id, text=f"You have successfully logged in!\nYour balance is {db_user.balance}")

        return {
            "message": "You have successfully logged in!",
            "user_id": db_user.id,
            "code": stored_code,
            "balance": db_user.balance
        }
    else:
        raise HTTPException(status_code=400, detail="Invalid code!")


@app.post("/Api/Login", response_model=dict)
async def login(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user.id).first()
    if db_user:
        return {"message": f"User {user.id} already registered.", "balance": db_user.balance}
    try:
        new_user = User(id=user.id)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {"message": f"User {user.id} registered successfully.", "balance": new_user.balance}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.get("/Api/CreditInfo")
async def get_credit_info(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        return {"balance": db_user.balance}
    else:
        raise HTTPException(status_code=404, detail="User not found")


@app.post("/Api/BuyCredits")
async def buy_credits(user_id: int, amount: float, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        db_user.balance += amount
        db.commit()
        return {"message": f"Balance updated by {amount} credits."}
    else:
        raise HTTPException(status_code=404, detail="User not found")


@app.get("/Api/IsAdmin")
async def is_admin(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        return {"is_admin": db_user.account_type == "admin"}
    else:
        raise HTTPException(status_code=404, detail="User not found")


@app.get("/Api/AllUsers")
async def get_all_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [{"id": user.id, "balance": user.balance} for user in users]


@app.get("/")
def send_html():
    return "I love you <3"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
