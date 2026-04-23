from sqlalchemy import (
    Column, Integer, String, Float, Text,
    ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from database import Base


# ──────────────────────────────────────────
# 1. 작목 마스터
# ──────────────────────────────────────────
class CropSpec(Base):
    __tablename__ = "crop_specs"

    spec_id           = Column(Integer, primary_key=True, autoincrement=True)
    crop_name         = Column(String(100), nullable=False)  # 프릴아이스
    seed_name         = Column(String(100), nullable=False)  # 크리스피아노
    valid_from        = Column(String(10),  nullable=False)  # 2025-09-01
    seedling_days     = Column(Integer, nullable=False)      # 육묘기간
    growing_days      = Column(Integer, nullable=False)      # 재배기간
    expected_weight_g = Column(Integer)                      # 예상중량(g)
    seeding_ratio     = Column(Float, nullable=False, default=1.2)  # 파종비율
    created_at        = Column(String(30), default="datetime('now')")

    # 이 spec을 참조하는 재배라인들
    cycles = relationship("GrowCycle", back_populates="spec")


# ──────────────────────────────────────────
# 2. 클러스터
# ──────────────────────────────────────────
class Cluster(Base):
    __tablename__ = "clusters"

    cluster_id   = Column(Integer, primary_key=True, autoincrement=True)
    cluster_name = Column(String(100), nullable=False, unique=True)  # 고양지축1
    is_active    = Column(Integer, default=1)
    created_at   = Column(String(30))

    farms = relationship("Farm", back_populates="cluster")


# ──────────────────────────────────────────
# 3. 농장 마스터
# ──────────────────────────────────────────
class Farm(Base):
    __tablename__ = "farms"

    farm_id            = Column(Integer, primary_key=True, autoincrement=True)
    farm_name          = Column(String(100), nullable=False, unique=True)
    cluster_id         = Column(Integer, ForeignKey("clusters.cluster_id"))
    # NULL = 개인농장 / 값 있으면 클러스터 소속

    # 출하 스케줄
    harvest_schedule   = Column(String(20), nullable=False)
    # 'mon_tue' → 정식:목, 파종:금, 수확:월화
    # 'wed_thu' → 정식:월, 파종:화, 수확:수목
    seeding_weekday    = Column(Integer, nullable=False)    # 0=월 ~ 6=일
    transplant_weekday = Column(Integer, nullable=False)
    harvest_weekday    = Column(Integer, nullable=False)

    # 농장 규격
    total_units        = Column(Integer, default=36)
    units_per_week     = Column(Float,   default=7.5)
    port_per_unit      = Column(Integer, default=256)
    seedling_box_unit  = Column(Integer, default=0)
    # 0 = 일반농장 (씨앗 단위 최소화)
    # 1 = 클러스터 (삽목상자 단위 역산)

    is_active  = Column(Integer, default=1)
    created_at = Column(String(30))

    # 관계
    cluster  = relationship("Cluster", back_populates="farms")
    zones    = relationship("RackZone", back_populates="farm")
    batches  = relationship("GrowBatch", back_populates="farm")
    cycles   = relationship("GrowCycle", back_populates="farm")
    crop_specs = relationship("FarmCropSpec", back_populates="farm")



# ──────────────────────────────────────────
# 4. 랙 구조 — 구역 / 랙 / 단
# ──────────────────────────────────────────
class RackZone(Base):
    __tablename__ = "rack_zones"

    zone_id    = Column(Integer, primary_key=True, autoincrement=True)
    farm_id    = Column(Integer, ForeignKey("farms.farm_id"), nullable=False)
    zone_no    = Column(Integer, nullable=False)   # 1, 2, 3, 4
    zone_label = Column(String(20), nullable=False) # '1구역'

    __table_args__ = (UniqueConstraint("farm_id", "zone_no"),)

    farm  = relationship("Farm", back_populates="zones")
    racks = relationship("Rack", back_populates="zone")


class Rack(Base):
    __tablename__ = "racks"

    rack_id    = Column(Integer, primary_key=True, autoincrement=True)
    zone_id    = Column(Integer, ForeignKey("rack_zones.zone_id"), nullable=False)
    rack_no    = Column(Integer, nullable=False)    # 1, 2
    rack_label = Column(String(20), nullable=False) # '1-1랙'

    __table_args__ = (UniqueConstraint("zone_id", "rack_no"),)

    zone  = relationship("RackZone", back_populates="racks")
    tiers = relationship("RackTier", back_populates="rack")


class RackTier(Base):
    __tablename__ = "rack_tiers"

    tier_id       = Column(Integer, primary_key=True, autoincrement=True)
    rack_id       = Column(Integer, ForeignKey("racks.rack_id"), nullable=False)
    tier_no       = Column(Integer, nullable=False)    # 1~6
    tier_label    = Column(String(30), nullable=False) # '1-1랙-1단'
    unit_count    = Column(Integer, default=1)         # 이 단의 유닛수
    port_per_unit = Column(Integer, default=256)       # 유닛당 포트수
    port_count    = Column(Integer, nullable=False)    # 총 포트수 (계산값)
    is_active     = Column(Integer, default=1)

    __table_args__ = (UniqueConstraint("rack_id", "tier_no"),)

    rack      = relationship("Rack", back_populates="tiers")
    positions = relationship("PlantingPosition", back_populates="tier")


# ──────────────────────────────────────────
# 5. 차수
# ──────────────────────────────────────────
class GrowBatch(Base):
    __tablename__ = "grow_batches"

    batch_id           = Column(Integer, primary_key=True, autoincrement=True)
    farm_id            = Column(Integer, ForeignKey("farms.farm_id"), nullable=False)
    batch_no           = Column(Integer, nullable=False)   # 1차, 2차...
    plan_seeding_at    = Column(String(10), nullable=False) # 파종 예정일
    plan_transplant_at = Column(String(10))                 # 정식 예정일 (자동계산)
    plan_harvest_at    = Column(String(10))                 # 수확 예정일 (자동계산)
    status             = Column(String(20), default="planned")
    # planned | seeded | transplanted | harvesting | done
    created_at = Column(String(30))
    updated_at = Column(String(30))

    __table_args__ = (UniqueConstraint("farm_id", "batch_no"),)

    farm   = relationship("Farm", back_populates="batches")
    cycles = relationship("GrowCycle", back_populates="batch")


# ──────────────────────────────────────────
# 6. 작목별 라인 (핵심 테이블)
# ──────────────────────────────────────────
class GrowCycle(Base):
    __tablename__ = "grow_cycles"

    cycle_id  = Column(Integer, primary_key=True, autoincrement=True)
    batch_id  = Column(Integer, ForeignKey("grow_batches.batch_id"), nullable=False)
    farm_id   = Column(Integer, ForeignKey("farms.farm_id"), nullable=False)
    spec_id   = Column(Integer, ForeignKey("crop_specs.spec_id"))

    # 작목 정보
    crop_name     = Column(String(100), nullable=False)  # 프릴아이스
    seed_name     = Column(String(100))                  # 크리스피아노
    gutter_type   = Column(String(50))                   # A타입(15cm)
    port_per_unit = Column(Integer)                      # 256

    # 계획 (네토그린 입력)
    plan_unit_alloc      = Column(Float)    # unit단위배분
    plan_transplant_qty  = Column(Integer)  # 필요 정식수량
    plan_seeding_qty     = Column(Integer)  # 필요 파종포트수
    plan_seedling_box    = Column(Integer)  # 필요 삽목상자

    # 실적 (농장주 입력, NULL = 계획대로)
    actual_seeding_at     = Column(String(10))
    actual_seeding_qty    = Column(Integer)
    actual_transplant_at  = Column(String(10))
    actual_transplant_qty = Column(Integer)
    actual_harvest_at     = Column(String(10))  # 수확 보정일

    # 알림사항 (작목별)
    seeding_notice    = Column(Text)  # 파종 알림사항
    transplant_notice = Column(Text)  # 정식 알림사항
    harvest_notice    = Column(Text)  # 수확 알림사항

    # 클러스터 전용 정식위치 지정 텍스트
    transplant_position = Column(Text)  # '2-1랙 ~ 3-1랙의 각 4단'

    notes      = Column(Text)
    created_at = Column(String(30))
    updated_at = Column(String(30))

    # 관계
    batch     = relationship("GrowBatch", back_populates="cycles")
    farm      = relationship("Farm", back_populates="cycles")
    spec      = relationship("CropSpec", back_populates="cycles")
    positions = relationship("PlantingPosition", back_populates="cycle")
    logs      = relationship("ChangeLog", back_populates="cycle")

    # ── 계산 프로퍼티 ──────────────────────
    @property
    def effective_transplant_qty(self):
        """실적 없으면 계획값 반환"""
        return self.actual_transplant_qty or self.plan_transplant_qty

    @property
    def effective_seeding_qty(self):
        return self.actual_seeding_qty or self.plan_seeding_qty

    @property
    def expected_harvest_kg(self):
        """예상 수확량 (kg) = 정식수 × 예상중량"""
        qty = self.effective_transplant_qty
        if qty and self.spec and self.spec.expected_weight_g:
            return round(qty * self.spec.expected_weight_g / 1000, 1)
        return None


# ──────────────────────────────────────────
# 7. 정식 위치 (개인농장 농장주 입력)
# ──────────────────────────────────────────
class PlantingPosition(Base):
    __tablename__ = "planting_positions"

    position_id = Column(Integer, primary_key=True, autoincrement=True)
    cycle_id    = Column(Integer, ForeignKey("grow_cycles.cycle_id"), nullable=False)
    tier_id     = Column(Integer, ForeignKey("rack_tiers.tier_id"), nullable=False)
    # rack_tiers를 직접 참조 → 드롭다운 선택 구조

    __table_args__ = (UniqueConstraint("cycle_id", "tier_id"),)
    # 같은 작목라인에 같은 단을 중복 등록 불가

    cycle = relationship("GrowCycle", back_populates="positions")
    tier  = relationship("RackTier",  back_populates="positions")


# ──────────────────────────────────────────
# 8. 변경 이력
# ──────────────────────────────────────────
class ChangeLog(Base):
    __tablename__ = "change_logs"

    log_id       = Column(Integer, primary_key=True, autoincrement=True)
    cycle_id     = Column(Integer, ForeignKey("grow_cycles.cycle_id"))
    # NULL 가능 — batch 레벨 변경일 경우 cycle_id 없을 수 있음
    batch_id     = Column(Integer, ForeignKey("grow_batches.batch_id"))
    field_name   = Column(String(100), nullable=False)  # 변경된 컬럼명
    old_value    = Column(Text)
    new_value    = Column(Text)
    change_type  = Column(String(30), nullable=False)
    # 'exception'    운영팀 예외 접수
    # 'correction'   단순 수정
    # 'plan_update'  계획 자체 변경
    changed_by   = Column(String(100))  # 입력한 사람
    reason       = Column(Text)         # 변경 사유
    created_at   = Column(String(30))

    cycle = relationship("GrowCycle", back_populates="logs")

    # ──────────────────────────────────────────
# 9. 농장별 작목 스펙 오버라이드
# ──────────────────────────────────────────
class FarmCropSpec(Base):
    __tablename__ = "farm_crop_specs"

    farm_spec_id      = Column(Integer, primary_key=True, autoincrement=True)
    farm_id           = Column(Integer, ForeignKey("farms.farm_id"), nullable=False)
    crop_name         = Column(String(100), nullable=False)
    seed_name         = Column(String(100), nullable=False)
    valid_from        = Column(String(10), nullable=False)
    valid_until       = Column(String(10))
    seedling_days     = Column(Integer)
    growing_days      = Column(Integer)
    expected_weight_g = Column(Integer)
    seeding_ratio     = Column(Float)
    reason            = Column(Text)
    created_at        = Column(String(30))

    __table_args__ = (UniqueConstraint("farm_id", "crop_name", "seed_name", "valid_from"),)

    farm = relationship("Farm", back_populates="crop_specs")