
import threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from config import environments
from cron_service.scheduler import run_scheduler

from router.instagram_users import router


app = FastAPI(
    title=environments.settings.PROJECT_NAME,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        environments.settings.FRONTEND_HOST,
        environments.settings.DEFAULT_FRONTEND
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

limiter = Limiter(key_func=get_remote_address, default_limits=["10/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(SlowAPIMiddleware)

app.include_router(router)


@app.on_event("startup")
async def startup_event():
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
