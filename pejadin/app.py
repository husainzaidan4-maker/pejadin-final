import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")
app = FastAPI(title="PEJADIN Frontend")
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
