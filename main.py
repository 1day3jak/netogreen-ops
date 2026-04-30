from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="네토그린 운영 시스템")
templates = Jinja2Templates(directory="templates")

from routers import seeding, overview, farms
app.include_router(seeding.router)
app.include_router(overview.router)
app.include_router(farms.router)

@app.get("/")
def root():
    return RedirectResponse(url="/overview")