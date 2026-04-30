from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date, timedelta
from database import get_db
from models import Farm, FarmOwner, Cluster

router = APIRouter(prefix="/farms", tags=["farms"])
templates = Jinja2Templates(directory="templates")


# ── 농장 목록 화면 ────────────────────────
@router.get("/", response_class=HTMLResponse)
def farms_list(request: Request, db: Session = Depends(get_db)):
    farms    = db.query(Farm).order_by(Farm.farm_type, Farm.farm_code).all()
    clusters = db.query(Cluster).all()

    # SQLAlchemy 객체 → 딕셔너리 변환
    farms_json = [
        {
            "farm_id":            f.farm_id,
            "farm_code":          f.farm_code,
            "farm_type":          f.farm_type,
            "cluster_id":         f.cluster_id,
            "address":            f.address or '',
            "harvest_days":       f.harvest_days or '',
            "transplant_weekday": f.transplant_weekday,
            "harvest_weekday":    f.harvest_weekday,
            "seeding_weekday":    f.seeding_weekday,
            "total_units":        f.total_units,
            "units_per_week":     f.units_per_week,
            "port_per_unit":      f.port_per_unit,
            "total_ports":        f.total_ports,
            "farm_structure":     f.farm_structure or '',
            "seedling_box_unit":  f.seedling_box_unit,
            "is_active":          f.is_active,
            "farm_name":          f.current_owner.farm_name  if f.current_owner else '',
            "owner_name":         f.current_owner.owner_name if f.current_owner else '',
            "owner_phone":        f.current_owner.phone      if f.current_owner else '',
            "owner_email":        f.current_owner.email      if f.current_owner else '',
            "owner_started_at":   f.current_owner.started_at if f.current_owner else '',
        }
        for f in farms
    ]

    return templates.TemplateResponse(
        request=request,
        name="farms.html",
        context={
            "farms":      farms,       # 템플릿 표시용
            "farms_json": farms_json,  # JS openModal용
            "clusters":   clusters,
        }
    )

# ── 농장 저장 요청 모델 ───────────────────
class FarmSaveRequest(BaseModel):
    farm_id:           Optional[int]  = None
    farm_code:         str
    farm_type:         str            = 'general'
    cluster_id:        Optional[int]  = None
    address:           Optional[str]  = ""
    harvest_days:      str            = ""   # "0,1" 형태
    transplant_weekday: int
    harvest_weekday:   int
    seeding_weekday:   int
    total_units:       int
    units_per_week:    float
    port_per_unit:     int            = 256
    total_ports:       Optional[int]  = None
    farm_structure:    Optional[str]  = ""
    seedling_box_unit: int            = 0
    is_active:         int            = 1
    # 농장주 정보
    farm_name:         Optional[str]  = ""
    owner_name:        Optional[str]  = ""
    phone:             Optional[str]  = ""
    email:             Optional[str]  = ""
    started_at:        Optional[str]  = ""


# ── 농장 저장 API ─────────────────────────
@router.post("/save")
def save_farm(payload: FarmSaveRequest, db: Session = Depends(get_db)):
    now = datetime.now().isoformat()

    if payload.farm_id:
        farm = db.query(Farm).filter(Farm.farm_id == payload.farm_id).first()
        if not farm:
            return JSONResponse({"error": "농장을 찾을 수 없습니다."}, status_code=404)
    else:
        farm = Farm(created_at=now)
        db.add(farm)

    # 기본정보 업데이트
    farm.farm_code          = payload.farm_code
    farm.farm_type          = payload.farm_type
    farm.cluster_id         = payload.cluster_id
    farm.address            = payload.address
    farm.harvest_days       = payload.harvest_days
    farm.transplant_weekday = payload.transplant_weekday
    farm.harvest_weekday    = payload.harvest_weekday
    farm.seeding_weekday    = payload.seeding_weekday
    farm.total_units        = payload.total_units
    farm.units_per_week     = payload.units_per_week
    farm.port_per_unit      = payload.port_per_unit
    farm.total_ports        = payload.total_ports
    farm.farm_structure     = payload.farm_structure
    farm.seedling_box_unit  = payload.seedling_box_unit
    farm.is_active          = payload.is_active
    db.flush()

    # 농장주 정보 처리
    if payload.started_at:
        current_owner = db.query(FarmOwner).filter(
            FarmOwner.farm_id == farm.farm_id
        ).order_by(FarmOwner.started_at.desc()).first()

        if current_owner and current_owner.started_at == payload.started_at:
            # 시작일 같으면 현재 농장주 수정
            current_owner.farm_name  = payload.farm_name
            current_owner.owner_name = payload.owner_name
            current_owner.phone      = payload.phone
            current_owner.email      = payload.email
        else:
            # 시작일 다르면 새 농장주 추가
            if current_owner and not current_owner.ended_at:
                # 이전 농장주 종료일 = 새 시작일 전날
                prev_end = (date.fromisoformat(payload.started_at)
                            - timedelta(days=1)).isoformat()
                current_owner.ended_at = prev_end

            new_owner = FarmOwner(
                farm_id    = farm.farm_id,
                farm_name  = payload.farm_name,
                owner_name = payload.owner_name,
                phone      = payload.phone,
                email      = payload.email,
                started_at = payload.started_at,
                created_at = now,
            )
            db.add(new_owner)

    db.commit()
    return JSONResponse({"success": True, "farm_id": farm.farm_id})


# ── 농장주 이력 조회 API ──────────────────
@router.get("/owners/{farm_id}")
def get_owners(farm_id: int, db: Session = Depends(get_db)):
    owners = db.query(FarmOwner).filter(
        FarmOwner.farm_id == farm_id
    ).order_by(FarmOwner.started_at.desc()).all()

    return JSONResponse({
        "owners": [
            {
                "owner_id":  o.owner_id,
                "farm_name": o.farm_name  or '',
                "owner_name":o.owner_name or '',
                "phone":     o.phone      or '',
                "email":     o.email      or '',
                "started_at":o.started_at or '',
                "ended_at":  o.ended_at   or '현재',
            }
            for o in owners
        ]
    })


# ── 농장 활성/비활성 토글 ─────────────────
@router.post("/toggle/{farm_id}")
def toggle_farm(farm_id: int, db: Session = Depends(get_db)):
    farm = db.query(Farm).filter(Farm.farm_id == farm_id).first()
    if not farm:
        return JSONResponse({"error": "농장을 찾을 수 없습니다."}, status_code=404)
    farm.is_active = 0 if farm.is_active else 1
    db.commit()
    return JSONResponse({"success": True, "is_active": farm.is_active})


# ── 클러스터 저장 API ─────────────────────
class ClusterRequest(BaseModel):
    cluster_id:   Optional[int] = None
    cluster_name: str

@router.post("/cluster/save")
def save_cluster(payload: ClusterRequest, db: Session = Depends(get_db)):
    now = datetime.now().isoformat()
    if payload.cluster_id:
        cluster = db.query(Cluster).filter(
            Cluster.cluster_id == payload.cluster_id
        ).first()
    else:
        cluster = Cluster(created_at=now)
        db.add(cluster)

    cluster.cluster_name = payload.cluster_name
    db.commit()
    return JSONResponse({"success": True, "cluster_id": cluster.cluster_id})