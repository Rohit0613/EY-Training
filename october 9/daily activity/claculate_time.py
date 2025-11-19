from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
import logging
import time
import traceback

app = FastAPI()


logging.basicConfig(
    filename="app.log",
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)


visit_count = 0



@app.middleware("http")
async def log_and_time_requests(request: Request, call_next):
    global visit_count

    start_time = time.time()


    if request.url.path != "/visits":
        visit_count += 1
        logging.info(f"Visit {visit_count} times.")

    try:
        response: Response = await call_next(request)
    except Exception as e:
        duration = round(time.time() - start_time, 4)
        logging.error(
            f"Exception in {request.method} {request.url.path}: {str(e)}\n{traceback.format_exc()}"
        )
        raise e

    duration = round(time.time() - start_time, 4)
    response.headers["X-Process-Time"] = str(duration)

    logging.info(
        f"{request.method} {request.url.path} | Status: {response.status_code} | Duration: {duration}s"
    )

    return response



students = [{"id": 1, "name": "Rahul"}, {"id": 2, "name": "Neha"}]


@app.get("/students")
def get_students():
    logging.info("Fetching all students from database...")
    return students


@app.get("/visits")
def get_visits():
    return {"visit_count": visit_count}


@app.get("/error-demo")
def error_demo():
    raise ValueError("Simulated error for testing logs")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(
        f"Unhandled error in {request.url.path}: {str(exc)}\n{traceback.format_exc()}"
    )
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "detail": str(exc)},
    )