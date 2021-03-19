import os

import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.admin.endpoints import create_admin_endpoints, admin_router
from app.admin.schemas.user import UserList
from app.auth.crud.user_token import get_password_hash
from app.auth.endpoints import auth_router
from fastapi_sqlalchemy import DBSessionMiddleware
from fastapi_sqlalchemy import db

from app.auth.models import User
from app.auth.schema import UserData
from core.config import settings

origins = [
    "http://localhost:8081",
    "http://localhost:8082",
    "http://localhost:8082",
    "http://192.168.1.59:8081",
]

def create_app():
    app = FastAPI()
    app.add_middleware(DBSessionMiddleware, db_url=settings.DATABASE_URL)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(auth_router, prefix="/auth")
    create_admin_endpoints(app)
    return app


app = create_app()

@app.on_event("startup")
async def startup_event():
    print(get_password_hash('admin'))


@app.get("/", response_model=UserList)
async def index():
    users = db.session.query(User).all()
    result = UserList.parse_obj({"items": users})
    return result
