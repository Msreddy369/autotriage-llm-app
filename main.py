from fastapi import FastAPI

# Configure DSPy FIRST before importing anything that uses it
import config.dspy_setup

from routes import tasks

app = FastAPI()
app.include_router(tasks.router)
