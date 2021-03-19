import os
from pydantic import BaseSettings

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER_MODE = os.getenv("SERVER_MODE", "local")


class Settings(BaseSettings):
    app_name: str = "API_gateway"

    PORT: int
    HOST: str

    DATABASE_URL: str
    BASE_DIR: str = BASE_DIR
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_MINUTES: int

    class Config:
        env_file = f"{BASE_DIR}/.env.{SERVER_MODE}"


settings = Settings()
