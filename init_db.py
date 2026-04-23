from database import engine, Base, SessionLocal
from models import CropSpec, Farm, Cluster
from datetime import datetime

def init():
    # 테이블 전체 생성
    Base.metadata.create_all(bind=engine)
    print("테이블 생성 완료")

    db = SessionLocal()
    try:
        seed_crop_specs(db)
        seed_farms(db)
        db.commit()
        print("기초 데이터 입력 완료")
    finally:
        db.close()

def seed_crop_specs(db):
    """etc. 계산 시트 데이터 입력"""
    if db.query(CropSpec).first():
        print("crop_specs 이미 존재 — 스킵")
        return

    specs = [
        CropSpec(crop_name="프릴아이스",  seed_name="크리스피아노",
                 valid_from="2025-09-01", seedling_days=21, growing_days=35,
                 expected_weight_g=130,   seeding_ratio=1.2),
        CropSpec(crop_name="미니로메인",  seed_name="라벨로",
                 valid_from="2025-09-01", seedling_days=21, growing_days=35,
                 expected_weight_g=90,    seeding_ratio=1.2),
        CropSpec(crop_name="버터헤드",    seed_name="페어리",
                 valid_from="2025-09-01", seedling_days=21, growing_days=35,
                 expected_weight_g=90,    seeding_ratio=1.2),
        CropSpec(crop_name="카이피라",    seed_name="카이피라",
                 valid_from="2025-09-01", seedling_days=21, growing_days=35,
                 expected_weight_g=90,    seeding_ratio=1.2),
        CropSpec(crop_name="적프릴아이스", seed_name="스케맨더",
                 valid_from="2025-09-01", seedling_days=21, growing_days=35,
                 expected_weight_g=70,    seeding_ratio=1.2),
    ]
    db.add_all(specs)
    print(f"  crop_specs {len(specs)}건 입력")

def seed_farms(db):
    """파주1 농장 입력 (나머지는 추후 추가)"""
    if db.query(Farm).first():
        print("farms 이미 존재 — 스킵")
        return

    farms = [
        Farm(
            farm_name="파주1",
            cluster_id=None,           # 개인농장
            harvest_schedule="wed_thu", # 수목 출하
            seeding_weekday=1,          # 화요일
            transplant_weekday=0,       # 월요일
            harvest_weekday=2,          # 수요일
            total_units=48,
            units_per_week=9.5,
            port_per_unit=256,
            seedling_box_unit=0,        # 일반농장
            is_active=1,
            created_at=datetime.now().isoformat()
        ),
    ]
    db.add_all(farms)
    print(f"  farms {len(farms)}건 입력")

if __name__ == "__main__":
    init()