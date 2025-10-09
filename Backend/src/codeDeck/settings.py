from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):


    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix="app_"

    MONGO_DB_URL:str
    MONGO_DB_NAME:str
    JWT_SECRET_KEY:str

settings=AppSettings()