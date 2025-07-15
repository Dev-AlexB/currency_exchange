import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.api.endpoints.currency import currency_router
from app.api.endpoints.users import auth_router
from app.api.errors.handlers import handlers


app = FastAPI(exception_handlers=handlers)


app.include_router(currency_router)
app.include_router(auth_router)


@app.get("/")
async def index():
    return FileResponse("./index.html")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
