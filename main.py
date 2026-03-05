from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from config import *
from routers import auth, profile, posts, chats
from fastapi.staticfiles import StaticFiles



app = FastAPI()
# ВАЖНО: замените обработчик ошибок

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={
            "error": "Неверный формат файла",
            "details": [f"{err['loc']}: {err['msg']}" for err in exc.errors()]
        }
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8081",
                    "http://127.0.0.1:8081", 
                    "http://localhost:3000",
                    "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, tags=['auth'])
app.include_router(chats.router, tags=['сhats'])
app.include_router(posts.router, tags=['posts'])
app.include_router(profile.router, tags=['profile'])


@app.get('/')
def root():
    return "hello world"

app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=True)

