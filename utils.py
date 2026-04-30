import math
from datetime import date, timedelta

PORTS_PER_UNIT        = 256  # 유닛당 포트수 (15cm 거터커버 기준)
PORTS_PER_SEEDLING_BOX = 176  # 삽목상자당 포트수


# ──────────────────────────────────────────
# 수량 계산
# ──────────────────────────────────────────
def calc_quantities(unit_alloc: float, seeding_ratio: float,
                    ports_per_box: int = 176) -> dict:
    transplant_qty = int(unit_alloc * PORTS_PER_UNIT)
    raw_seeding    = math.ceil(transplant_qty * seeding_ratio)
    seeding_qty    = raw_seeding
    seedling_boxes = math.ceil(seeding_qty / ports_per_box)

    return {
        "plan_transplant_qty": transplant_qty,
        "plan_seeding_qty":    seeding_qty,
        "plan_seedling_box":   seedling_boxes,
    }


# ──────────────────────────────────────────
# 날짜 계산
# ──────────────────────────────────────────
def calc_transplant_date(seeding_date: date, seedling_days: int,
                         transplant_weekday: int) -> date:
    """
    파종일 + 육묘기간 → 정식 요일에 맞게 앞당김
    weekday: 0=월 1=화 2=수 3=목 4=금 5=토 6=일
    """
    raw  = seeding_date + timedelta(days=seedling_days)
    diff = (raw.weekday() - transplant_weekday) % 7
    return raw - timedelta(days=diff)


def calc_harvest_date(transplant_date: date, growing_days: int,
                      harvest_weekday: int) -> date:
    """
    정식일 + 재배기간 → 수확 요일에 맞게 앞당김
    """
    raw  = transplant_date + timedelta(days=growing_days)
    diff = (raw.weekday() - harvest_weekday) % 7
    return raw - timedelta(days=diff)


# ──────────────────────────────────────────
# spec 조회 (공통 → 농장별 오버라이드)
# ──────────────────────────────────────────
def get_effective_spec(db, farm_id: int, crop_name: str,
                       seed_name: str, seeding_date: date) -> dict | None:
    """
    파종일 기준으로 유효한 spec 반환
    농장별 오버라이드 있으면 우선 적용, 없으면 공통값 사용
    NULL 필드는 공통값으로 채움
    """
    from models import FarmCropSpec, CropSpec

    # 1. 공통 기본값
    base_spec = db.query(CropSpec).filter(
        CropSpec.crop_name == crop_name,
        CropSpec.seed_name == seed_name,
        CropSpec.valid_from <= seeding_date.isoformat()
    ).order_by(CropSpec.valid_from.desc()).first()

    if not base_spec:
        return None

    # 2. 농장별 오버라이드 확인
    farm_spec = db.query(FarmCropSpec).filter(
        FarmCropSpec.farm_id   == farm_id,
        FarmCropSpec.crop_name == crop_name,
        FarmCropSpec.seed_name == seed_name,
        FarmCropSpec.valid_from  <= seeding_date.isoformat(),
        (FarmCropSpec.valid_until == None) |
        (FarmCropSpec.valid_until >= seeding_date.isoformat())
    ).order_by(FarmCropSpec.valid_from.desc()).first()

    # 3. 오버라이드 없으면 공통값 그대로
    if not farm_spec:
        return {
            "seedling_days":     base_spec.seedling_days,
            "growing_days":      base_spec.growing_days,
            "expected_weight_g": base_spec.expected_weight_g,
            "seeding_ratio":     base_spec.seeding_ratio,
        }

    # 4. 오버라이드 있으면 NULL 필드만 공통값으로 채움
    return {
        "seedling_days":     farm_spec.seedling_days     or base_spec.seedling_days,
        "growing_days":      farm_spec.growing_days      or base_spec.growing_days,
        "expected_weight_g": farm_spec.expected_weight_g or base_spec.expected_weight_g,
        "seeding_ratio":     farm_spec.seeding_ratio     or base_spec.seeding_ratio,
    }


# ──────────────────────────────────────────
# 한 번에 모두 계산
# ──────────────────────────────────────────
def calc_all(db, farm_id: int, crop_name: str, seed_name: str,
             unit_alloc: float, seeding_date: date,
             seedling_box_unit: bool = False) -> dict | None:
    """
    유닛배분 + 파종일 입력 → 모든 값 한번에 계산해서 반환

    반환값 예시:
    {
        "plan_transplant_qty": 1280,
        "plan_seeding_qty":    1536,
        "plan_seedling_box":   9,
        "plan_transplant_at":  "2026-03-16",
        "plan_harvest_at":     "2026-04-15",
        "expected_weight_g":   130,
        "seeding_ratio":       1.2,
    }
    """
    from models import Farm

    farm = db.query(Farm).filter(Farm.farm_id == farm_id).first()
    if not farm:
        return None

    spec = get_effective_spec(db, farm_id, crop_name, seed_name, seeding_date)
    if not spec:
        return None

    quantities = calc_quantities(
        unit_alloc, spec["seeding_ratio"], farm.seedling_box_unit
    )
    transplant_date = calc_transplant_date(
        seeding_date, spec["seedling_days"], farm.transplant_weekday
    )
    harvest_date = calc_harvest_date(
        transplant_date, spec["growing_days"], farm.harvest_weekday
    )

    return {
        **quantities,
        "plan_transplant_at":  transplant_date.isoformat(),
        "plan_harvest_at":     harvest_date.isoformat(),
        "expected_weight_g":   spec["expected_weight_g"],
        "seeding_ratio":       spec["seeding_ratio"],
    }


# ──────────────────────────────────────────
# 변경 이력 기록
# ──────────────────────────────────────────
def log_change(db, field_name: str, old_value, new_value,
               change_type: str, changed_by: str, reason: str,
               cycle_id: int = None, batch_id: int = None):
    """
    변경 이력 기록 — cycle 또는 batch 레벨 모두 가능
    """
    from models import ChangeLog
    from datetime import datetime

    log = ChangeLog(
        cycle_id    = cycle_id,
        batch_id    = batch_id,
        field_name  = field_name,
        old_value   = str(old_value) if old_value is not None else None,
        new_value   = str(new_value) if new_value is not None else None,
        change_type = change_type,
        changed_by  = changed_by,
        reason      = reason,
        created_at  = datetime.now().isoformat()
    )
    db.add(log)
    # commit은 호출하는 쪽에서 처리