import os
from fastapi import FastAPI
from dotenv import load_dotenv
from database.database import init_db
from src.routes import router

load_dotenv()
app = FastAPI()
app.include_router(router=router)


@app.on_event("startup")
async def startup_event():
    await init_db()


@app.get("/")
def send_html():
    return "I love you <3"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
