from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database.schemas import UserCreate, GenerateCodeRequest, VerificationCodeRequest, DestroyCodeRequest
from src.services import (
    generate_code_service,
    recall_code_service,
    validate_code_service,
    login_service,
    get_credit_info_service,
    buy_credits_service,
    is_admin_service,
    get_all_users_service
)
from database.database import get_db

router = APIRouter()


@router.post("/Api/DestroyCode")
async def recall_code(request: DestroyCodeRequest, db: AsyncSession = Depends(get_db)):
    return await recall_code_service(request, db)


@router.post("/Api/RequestCode")
async def generate_code(request: GenerateCodeRequest, db: AsyncSession = Depends(get_db)):
    return await generate_code_service(request, db)


@router.post("/Api/ValidateCode")
async def validate_code(request: VerificationCodeRequest, db: AsyncSession = Depends(get_db)):
    return await validate_code_service(request, db)


@router.post("/Api/Login")
async def login(user: UserCreate, db: AsyncSession = Depends(get_db)):
    return await login_service(user, db)


@router.get("/Api/CheckCredits")
async def get_credit_info(user_id: int, db: AsyncSession = Depends(get_db)):
    return await get_credit_info_service(user_id, db)


@router.post("/Api/BuyCredits")
async def buy_credits(user_id: int, amount: float, db: AsyncSession = Depends(get_db)):
    return await buy_credits_service(user_id, amount, db)


@router.get("/Api/IsAdmin")
async def is_admin(user_id: int, db: AsyncSession = Depends(get_db)):
    return await is_admin_service(user_id, db)


@router.get("/Api/AllUsers")
async def get_all_users(db: AsyncSession = Depends(get_db)):
    return await get_all_users_service(db)