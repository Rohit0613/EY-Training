from fastapi import FastAPI
import asyncio
import time

app = FastAPI()

@app.get("/sync-task")
def sync_task():
    time.sleep(10)
    return {"message": "Sync task completed after 5 sec"}

@app.get("/async-task")
async def async_task():
    await asyncio.sleep(10)
    return {"message": "Async task completed after 5 sec"}