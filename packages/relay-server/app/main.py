from __future__ import annotations

import logging

from fastapi import FastAPI

from app.routes.notify import router

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Flux Notifier Relay Server",
    description="APNs/FCM mobile push relay for Flux Notifier",
    version="0.1.0",
)

app.include_router(router)
