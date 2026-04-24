from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import date, timedelta
from database import get_db
from models import Farm, GrowBatch, GrowCycle

router = APIRouter(prefix="/overview", tags=["overview"])
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
def supply_overview(
    request: Request,
    db:      Session = Depends(get_db),
    farm_id: int     = None,
):
    query = db.query(GrowBatch).join(Farm)

    if farm_id:
        query = query.filter(GrowBatch.farm_id == farm_id)

    query = query.filter(
        (GrowBatch.status != "done") |
        (GrowBatch.plan_harvest_at >= (date.today() - timedelta(days=30)).isoformat())
    )

    batches = query.order_by(GrowBatch.plan_harvest_at).all()
    farms   = db.query(Farm).filter(Farm.is_active == 1).all()

    today = date.today()
    for batch in batches:
        if batch.plan_harvest_at:
            harvest = date.fromisoformat(batch.plan_harvest_at)
            batch.days_to_harvest = (harvest - today).days
        else:
            batch.days_to_harvest = None

    return templates.TemplateResponse(
        request=request,
        name="overview.html",
        context={
            "batches":          batches,
            "farms":            farms,
            "selected_farm_id": farm_id,
            "today":            today,
        }
    )