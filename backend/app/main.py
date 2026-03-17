from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import statistics_router, dashboard_router

routers = [
    statistics_router,
    dashboard_router
]

app = FastAPI()
for router in routers:
    app.include_router(router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://frontend.localhost",
        "http://frontend.localhost:80",
        "https://frontend.localhost",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
