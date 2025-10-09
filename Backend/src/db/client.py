from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase
from fastapi import FastAPI 
from typing import Any,cast

class MongoDBClient:
    _instance=None
    mongodb:AsyncDatabase

    def __new__(cls)->"MongoDBClient":
        if cls._instance is None:
            cls._instance=super().__new__(cls)
            app=get_current_app()
            cls._instance.mongodb=app.mongodb
        return cls._instance


def get_current_app()->FastAPI:
    import importlib
    main_module = importlib.import_module("src.main")
    field="app"
    return cast(FastAPI, getattr(main_module, field))
