from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database.schemas import GenerateCodeRequest, UserRequest
from src.services import (
    generate_code_service,
    recall_code_service,
    get_credit_info_service
)
from database.database import get_db

router = APIRouter()


@router.post("/Api/DestroyCode")
async def recall_code(request: UserRequest, db: AsyncSession = Depends(get_db)):
    return await recall_code_service(request.account, request.code, db)


@router.post("/Api/RequestCode")
async def generate_code(request: GenerateCodeRequest, db: AsyncSession = Depends(get_db)):
    return await generate_code_service(request.account, db)


@router.post("/Api/CheckCredits")
async def get_credit_info(request: UserRequest, db: AsyncSession = Depends(get_db)):
    return await get_credit_info_service(request.account, request.code, db)
