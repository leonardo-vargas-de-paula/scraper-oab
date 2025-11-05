import os
from fastapi import FastAPI



app = FastAPI()

from app.routes.fetch_routes import fetch_routes

app.include_router(fetch_routes)