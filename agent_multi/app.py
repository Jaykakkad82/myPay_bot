from fastapi import FastAPI
from .routes.chat import router as chat_router
from .routes.approval import router as approval_router
from .routes.session import router as session_router

# python
from fastapi.middleware.cors import CORSMiddleware
from .runtime.config import CORS_ORIGINS

app = FastAPI()
app.include_router(chat_router)
app.include_router(session_router)
app.include_router(approval_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,  # or specify allowed origins
    allow_methods=["*"],
    allow_headers=["*"],
)
