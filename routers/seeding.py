from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, timedelta, datetime
from database import get_db
from models import Farm, GrowBatch, GrowCycle, CropSpec

router = APIRouter(prefix="/seeding", tags=["seeding"])
templates = Jinja2Templates(directory="templates")


# ── 파종계획 입력/수정 화면 ──────────────────
@router.get("/", response_class=HTMLResponse)
def seeding_form(request: Request, db: Session = Depends(get_db)):
    farms      = db.query(Farm).filter(Farm.is_active == 1).all()
    crop_specs = db.query(CropSpec).all()

    crop_specs_json = [
        {
            "crop_name":         s.crop_name,
            "seed_name":         s.seed_name,
            "seedling_days":     s.seedling_days,
            "growing_days":      s.growing_days,
            "expected_weight_g": s.expected_weight_g,
            "seeding_ratio":     s.seeding_ratio,
        }
        for s in crop_specs
    ]

    return templates.TemplateResponse(
        request=request,
        name="seeding_form.html",
        context={
            "farms":      farms,
            "crop_specs": crop_specs_json,
        }
    )


# ── 기존 데이터 로드 API ──────────────────────
@router.get("/load")
def load_seeding_data(
    farm_id: int,
    mode:    str     = "current",
    db:      Session = Depends(get_db)
):
    query = db.query(GrowCycle).join(GrowBatch).filter(
        GrowCycle.farm_id == farm_id
    )

    if mode == "current":
        today  = date.today()
        mon    = today - timedelta(days=today.weekday())
        cutoff = (mon - timedelta(days=14)).isoformat()
        query  = query.filter(
            (GrowBatch.plan_harvest_at >= cutoff) |
            (GrowBatch.plan_harvest_at == None)
        )

    cycles = query.outerjoin(CropSpec, GrowCycle.spec_id == CropSpec.spec_id)\
            .order_by(GrowBatch.batch_no, CropSpec.sort_order)\
            .all()

    rows = []
    for c in cycles:
        rows.append({
            "cycle_id":          c.cycle_id,
            "batch_no":          c.batch.batch_no,
            "crop_name":         c.crop_name,
            "seed_name":         c.seed_name       or '',
            "unit_alloc":        c.plan_unit_alloc  or '',
            "seeding_date":      c.batch.plan_seeding_at    or '',
            "transplant_qty":    c.plan_transplant_qty or '',
            "seeding_qty":       c.plan_seeding_qty    or '',
            "seedling_boxes":    c.plan_seedling_box   or '',
            "seedling_days":     c.spec.seedling_days if c.spec else '',
            "transplant_date":   c.batch.plan_transplant_at or '',
            "growing_days":      c.spec.growing_days  if c.spec else '',
            "harvest_date":      c.batch.plan_harvest_at    or '',
            "seeding_notice":    c.seeding_notice    or '',
            "transplant_notice": c.transplant_notice or '',
            "harvest_notice":    c.harvest_notice    or '',
        })

    return JSONResponse({"rows": rows})


# ── 저장 요청 모델 ────────────────────────────
class CropRow(BaseModel):
    cycle_id:          Optional[int] = None  # 있으면 수정, 없으면 신규
    batch_no:          int
    crop_name:         str
    seed_name:         str
    unit_alloc:        float
    seeding_date:      str
    transplant_qty:    Optional[int] = None
    seeding_qty:       Optional[int] = None
    seedling_boxes:    Optional[int] = None
    transplant_date:   Optional[str] = None
    harvest_date:      Optional[str] = None
    seeding_notice:    Optional[str] = ""
    transplant_notice: Optional[str] = ""
    harvest_notice:    Optional[str] = ""

class BatchSaveRequest(BaseModel):
    farm_id: int
    rows:    List[CropRow]


# ── 저장 API ──────────────────────────────────
@router.post("/batch")
def save_batch(payload: BatchSaveRequest, db: Session = Depends(get_db)):
    saved = 0

    for row in payload.rows:
        if row.cycle_id:
            # 기존 행 수정
            cycle = db.query(GrowCycle).filter(
                GrowCycle.cycle_id == row.cycle_id
            ).first()
            if cycle:
                cycle.crop_name           = row.crop_name
                cycle.seed_name           = row.seed_name
                cycle.plan_unit_alloc     = row.unit_alloc
                cycle.plan_transplant_qty = row.transplant_qty
                cycle.plan_seeding_qty    = row.seeding_qty
                cycle.plan_seedling_box   = row.seedling_boxes
                cycle.actual_seeding_at   = row.seeding_date
                cycle.actual_transplant_at = row.transplant_date
                cycle.actual_harvest_at   = row.harvest_date
                cycle.seeding_notice      = row.seeding_notice
                cycle.transplant_notice   = row.transplant_notice
                cycle.harvest_notice      = row.harvest_notice
                cycle.updated_at          = datetime.now().isoformat()
                saved += 1
            continue

        # 신규 행 — batch 있으면 재사용, 없으면 생성
        batch = db.query(GrowBatch).filter(
            GrowBatch.farm_id  == payload.farm_id,
            GrowBatch.batch_no == row.batch_no
        ).first()

        if not batch:
            batch = GrowBatch(
                farm_id        = payload.farm_id,
                batch_no       = row.batch_no,
                plan_seeding_at = row.seeding_date,
                status         = "planned",
                created_at     = datetime.now().isoformat(),
                updated_at     = datetime.now().isoformat(),
            )
            db.add(batch)
            db.flush()

        cycle = GrowCycle(
            batch_id               = batch.batch_id,
            farm_id                = payload.farm_id,
            crop_name              = row.crop_name,
            seed_name              = row.seed_name,
            plan_unit_alloc        = row.unit_alloc,
            plan_transplant_qty    = row.transplant_qty,
            plan_seeding_qty       = row.seeding_qty,
            plan_seedling_box      = row.seedling_boxes,
            actual_seeding_at      = row.seeding_date,
            actual_transplant_at   = row.transplant_date,
            actual_harvest_at      = row.harvest_date,
            seeding_notice         = row.seeding_notice,
            transplant_notice      = row.transplant_notice,
            harvest_notice         = row.harvest_notice,
            created_at             = datetime.now().isoformat(),
            updated_at             = datetime.now().isoformat(),
        )
        db.add(cycle)
        saved += 1

    db.commit()
    return JSONResponse({"saved": saved})


# ──삭제 API ──────────────────────────────────
class DeleteRequest(BaseModel):
    cycle_ids: List[int]

@router.post("/delete")
def delete_cycles(payload: DeleteRequest, db: Session = Depends(get_db)):
    deleted = 0
    for cycle_id in payload.cycle_ids:
        cycle = db.query(GrowCycle).filter(
            GrowCycle.cycle_id == cycle_id
        ).first()
        if cycle:
            batch = cycle.batch
            db.delete(cycle)
            db.flush()
            # 해당 차수에 더 이상 작목이 없으면 차수도 삭제
            remaining = db.query(GrowCycle).filter(
                GrowCycle.batch_id == batch.batch_id
            ).count()
            if remaining == 0:
                db.delete(batch)
            deleted += 1

    db.commit()
    return JSONResponse({"deleted": deleted})
