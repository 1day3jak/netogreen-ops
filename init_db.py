from database import engine, Base, SessionLocal
from models import CropSpec, Farm, Cluster, FarmOwner
from datetime import datetime


def init():
    Base.metadata.create_all(bind=engine)
    print("테이블 생성 완료")
    db = SessionLocal()
    try:
        seed_crop_specs(db)
        seed_clusters(db)
        seed_farms(db)
        db.commit()
        print("기초 데이터 입력 완료")
    except Exception as e:
        db.rollback()
        print(f"오류 발생: {e}")
        raise
    finally:
        db.close()


def seed_crop_specs(db):
    if db.query(CropSpec).first():
        print("crop_specs 이미 존재 — 스킵")
        return
    specs = [
        CropSpec(crop_name="프릴아이스",   seed_name="크리스피아노",
                 valid_from="2025-09-01", seedling_days=21, growing_days=35,
                 expected_weight_g=130,   seeding_ratio=1.2, sort_order=1),
        CropSpec(crop_name="미니로메인",   seed_name="라벨로",
                 valid_from="2025-09-01", seedling_days=21, growing_days=35,
                 expected_weight_g=90,    seeding_ratio=1.2, sort_order=2),
        CropSpec(crop_name="버터헤드",     seed_name="페어리",
                 valid_from="2025-09-01", seedling_days=21, growing_days=35,
                 expected_weight_g=90,    seeding_ratio=1.2, sort_order=3),
        CropSpec(crop_name="카이피라",     seed_name="카이피라",
                 valid_from="2025-09-01", seedling_days=21, growing_days=35,
                 expected_weight_g=90,    seeding_ratio=1.2, sort_order=4),
        CropSpec(crop_name="적프릴아이스", seed_name="스케맨더",
                 valid_from="2025-09-01", seedling_days=21, growing_days=35,
                 expected_weight_g=70,    seeding_ratio=1.2, sort_order=5),
    ]
    db.add_all(specs)
    db.flush()
    print(f"  crop_specs {len(specs)}건 입력")


def seed_clusters(db):
    if db.query(Cluster).first():
        print("clusters 이미 존재 — 스킵")
        return
    cluster = Cluster(
        cluster_name = "고양지축1",
        is_active    = 1,
        created_at   = datetime.now().isoformat()
    )
    db.add(cluster)
    db.flush()
    print("  clusters 1건 입력")


def seed_farms(db):
    if db.query(Farm).first():
        print("farms 이미 존재 — 스킵")
        return

    cluster = db.query(Cluster).filter(Cluster.cluster_name == "고양지축1").first()
    now = datetime.now().isoformat()

    # 출하요일 → 정식/수확/파종 요일 매핑
    # 수목 출하: 정식=월(0), 수확=수(2), 파종=화(1)
    # 월화 출하: 정식=목(3), 수확=월(0), 파종=금(4)
    def get_weekdays(harvest_schedule):
        if harvest_schedule == "수목":
            return dict(harvest_days="2,3", transplant_weekday=0,
                        harvest_weekday=2, seeding_weekday=1)
        else:  # 월화
            return dict(harvest_days="0,1", transplant_weekday=3,
                        harvest_weekday=0, seeding_weekday=4)

    farms_data = [
        # 일반농장
        dict(farm_code="화성2",   farm_type="general", schedule="수목",
             total_units=36,  units_per_week=7.2, port_per_unit=256, total_ports=9216,
             farm_structure="1유닛*6단*3랙",
             farm_name="그린픽",        owner_name="박연미", phone="010-9449-6105",
             email="meya2000@naver.com",
             address="경기 화성시 동탄첨단산업1로 27 금강펜테리움아이엑스타워 지하 1층 C동 144호",
             started_at="2026-01-01"),
        dict(farm_code="진안1",   farm_type="general", schedule="수목",
             total_units=36,  units_per_week=7.2, port_per_unit=256, total_ports=9216,
             farm_structure="1유닛*6단*3랙",
             farm_name="좋은환경농업",   owner_name="류슬기", phone="010-3411-1045",
             email="isogravity@naver.com",
             address="전북 진안군 진안읍 물곡리 784-1",
             started_at="2024-01-01"),
        dict(farm_code="수원1",   farm_type="general", schedule="수목",
             total_units=30,  units_per_week=6.0, port_per_unit=256, total_ports=7680,
             farm_structure="1유닛*5단*3랙",
             farm_name="형제의새벽",     owner_name="박환구", phone="010-2924-7030",
             email="parkhg7030@naver.com",
             address="경기도 수원시 영통구 매영로159번길 19 광교더퍼스트 지하1층 B07",
             started_at="2024-01-01"),
        dict(farm_code="화성4",   farm_type="general", schedule="월화",
             total_units=36,  units_per_week=7.2, port_per_unit=256, total_ports=9216,
             farm_structure="1유닛*6단*3랙",
             farm_name="해피팜프로젝트", owner_name="해피팜", phone="010-4175-6188",
             email="hello@openshare.kr",
             address="경기 화성시 동탄첨단산업1로 14 동탄케이밸리 312호",
             started_at="2024-01-01"),
        dict(farm_code="고양1",   farm_type="general", schedule="월화",
             total_units=36,  units_per_week=7.2, port_per_unit=256, total_ports=9216,
             farm_structure="1유닛*6단*3랙",
             farm_name="마녀팜",        owner_name="박오희", phone="010-3009-5252",
             email="parkouhee@naver.com",
             address="경기 고양시 덕양구 향동로 218 현대테라타워 DMC B2 91, 92호",
             started_at="2024-01-01"),
        dict(farm_code="대구1",   farm_type="general", schedule="월화",
             total_units=36,  units_per_week=7.2, port_per_unit=256, total_ports=9216,
             farm_structure="1유닛*6단*3랙",
             farm_name="그린킷",        owner_name="정재영", phone="010-3823-3540",
             email="umsjjy1@naver.com",
             address="대구 서구 와룡로 307 디센터1976 B219호",
             started_at="2024-01-01"),
        dict(farm_code="남양주1", farm_type="general", schedule="수목",
             total_units=48,  units_per_week=7.2, port_per_unit=256, total_ports=12288,
             farm_structure="1유닛*6단*4랙",
             farm_name="프롬씨드",      owner_name="정윤선", phone="010-2620-0502",
             email="ets0502@gmail.com",
             address="경기도 남양주시 다산순환로 20 현대프리미어캠퍼스 E동 431호",
             started_at="2024-01-01"),
        dict(farm_code="남양주2", farm_type="general", schedule="월화",
             total_units=48,  units_per_week=7.2, port_per_unit=256, total_ports=12288,
             farm_structure="1유닛*6단*4랙",
             farm_name="프롬씨드",      owner_name="정윤선", phone="010-2620-0502",
             email="ets0502@gmail.com",
             address="경기도 남양주시 다산순환로 20 현대프리미어캠퍼스 E동 432호",
             started_at="2024-01-01"),
        dict(farm_code="남양주3", farm_type="general", schedule="월화",
             total_units=36,  units_per_week=7.2, port_per_unit=256, total_ports=9216,
             farm_structure="1유닛*6단*3랙",
             farm_name="스페이스그리니", owner_name="권정윤", phone="010-4624-8712",
             email="jeongyunkwon@naver.com",
             address="경기 남양주시 다산지금로 202 현대테라타워 DIMC B동 601호",
             started_at="2025-01-01"),
        dict(farm_code="고양2",   farm_type="general", schedule="월화",
             total_units=30,  units_per_week=6.0, port_per_unit=256, total_ports=7680,
             farm_structure="1유닛*5단*3랙",
             farm_name="그루팜",        owner_name="차정호", phone="010-8311-6908",
             email="ja6907@naver.com",
             address="경기 고양시 덕양구 향기로 180 DMC 마스터원 909~910호",
             started_at="2025-01-01"),
        dict(farm_code="고양3",   farm_type="general", schedule="수목",
             total_units=36,  units_per_week=7.2, port_per_unit=256, total_ports=9216,
             farm_structure="1유닛*6단*3랙",
             farm_name="우리집팜",      owner_name="이상윤", phone="010-7431-6782",
             email="sangyun_ee@naver.com",
             address="경기 고양시 덕양구 향기로 180 DMC 마스터원 1413~1414호",
             started_at="2025-01-01"),
        dict(farm_code="고양4",   farm_type="general", schedule="수목",
             total_units=36,  units_per_week=7.2, port_per_unit=256, total_ports=9216,
             farm_structure="1유닛*6단*3랙",
             farm_name="코메스월드",     owner_name="석진환", phone="010-2584-1119",
             email="smend1119@naver.com",
             address="경기 고양시 덕양구 동축로 60 에이스하이엔드타워 지축역 215호",
             started_at="2025-01-01"),
        dict(farm_code="화성5",   farm_type="general", schedule="월화",
             total_units=36,  units_per_week=7.2, port_per_unit=256, total_ports=9216,
             farm_structure="1유닛*6단*3랙",
             farm_name="기류솔루션",     owner_name="김준영", phone="010-8991-6930",
             email="bizmeka3055@naver.com",
             address="경기 화성시 동탄첨단산업1로 14 동탄케이밸리 905호",
             started_at="2025-01-01"),
        dict(farm_code="평택1",   farm_type="general", schedule="월화",
             total_units=36,  units_per_week=7.2, port_per_unit=256, total_ports=9216,
             farm_structure="1유닛*6단*3랙",
             farm_name="에코루트",       owner_name="김경진", phone="010-4783-5280",
             email="dmldsl@hanmail.net",
             address="경기 평택시 진위2산단로 140 더퍼스트타워 515호",
             started_at="2025-01-01"),
        dict(farm_code="경광주1", farm_type="general", schedule="수목",
             total_units=36,  units_per_week=7.2, port_per_unit=256, total_ports=9216,
             farm_structure="1유닛*6단*3랙",
             farm_name="듀팜",          owner_name="박주찬", phone="010-2491-5786",
             email="dpceo1234@naver.com",
             address="경기 광주시 고산길 5",
             started_at="2025-01-01"),
        dict(farm_code="파주1",   farm_type="general", schedule="수목",
             total_units=48,  units_per_week=7.2, port_per_unit=256, total_ports=12288,
             farm_structure="1유닛*6단*4랙",
             farm_name="순수식물공장",   owner_name="최인호", phone="010-2269-9229",
             email="cos310915@gmail.com",
             address="경기도 파주시 봉암리 777-3",
             started_at="2025-01-01"),
        # 클러스터 농장
        dict(farm_code="B211호",  farm_type="cluster", schedule="월화",
             cluster_id=cluster.cluster_id,
             total_units=30,  units_per_week=None, port_per_unit=224, total_ports=6720,
             farm_structure="1유닛(224)*6단*2.5랙",
             farm_name="성수개발", owner_name="성수개발", phone=None,
             email=None, address=None, started_at="2025-01-01"),
        dict(farm_code="115호",   farm_type="cluster", schedule="월화",
             cluster_id=cluster.cluster_id,
             total_units=36,  units_per_week=None, port_per_unit=192, total_ports=6912,
             farm_structure="1유닛(192)*6단*3랙",
             farm_name="성수개발", owner_name="성수개발", phone=None,
             email=None, address=None, started_at="2025-01-01"),
        dict(farm_code="B111호",  farm_type="cluster", schedule="월화",
             cluster_id=cluster.cluster_id,
             total_units=60,  units_per_week=None, port_per_unit=192, total_ports=11520,
             farm_structure="1유닛(192)*6단*5랙",
             farm_name="성수개발", owner_name="성수개발", phone=None,
             email=None, address=None, started_at="2025-01-01"),
        dict(farm_code="B104호",  farm_type="cluster", schedule="월화",
             cluster_id=cluster.cluster_id,
             total_units=36,  units_per_week=None, port_per_unit=160, total_ports=5760,
             farm_structure="1유닛(160)*6단*3랙",
             farm_name="성수개발", owner_name="성수개발", phone=None,
             email=None, address=None, started_at="2025-01-01"),
        dict(farm_code="516호",   farm_type="cluster", schedule="월화",
             cluster_id=cluster.cluster_id,
             total_units=36,  units_per_week=None, port_per_unit=192, total_ports=6912,
             farm_structure="1유닛(192)*6단*3랙",
             farm_name="성수개발", owner_name="성수개발", phone=None,
             email=None, address=None, started_at="2025-01-01"),
        dict(farm_code="401호",   farm_type="cluster", schedule="월화",
             cluster_id=cluster.cluster_id,
             total_units=84,  units_per_week=None, port_per_unit=None, total_ports=14976,
             farm_structure="1유닛(192)*6단*4랙 + 1유닛(160)*6단*3랙",
             farm_name="성수개발", owner_name="성수개발", phone=None,
             email=None, address=None, started_at="2025-01-01"),
        dict(farm_code="404호",   farm_type="cluster", schedule="월화",
             cluster_id=cluster.cluster_id,
             total_units=36,  units_per_week=None, port_per_unit=192, total_ports=6912,
             farm_structure="1유닛(192)*6단*3랙",
             farm_name="성수개발", owner_name="성수개발", phone=None,
             email=None, address=None, started_at="2025-01-01"),
        dict(farm_code="B212호",  farm_type="cluster", schedule="월화",
             cluster_id=cluster.cluster_id,
             total_units=30,  units_per_week=None, port_per_unit=160, total_ports=4800,
             farm_structure="1유닛(160)*6단*2.5랙",
             farm_name="성수개발", owner_name="성수개발", phone=None,
             email=None, address=None, started_at="2025-01-01"),
    ]

    for d in farms_data:
        wd = get_weekdays(d["schedule"])
        farm = Farm(
            farm_code          = d["farm_code"],
            farm_type          = d["farm_type"],
            cluster_id         = d.get("cluster_id"),
            address            = d.get("address") or "",
            harvest_days       = wd["harvest_days"],
            transplant_weekday = wd["transplant_weekday"],
            harvest_weekday    = wd["harvest_weekday"],
            seeding_weekday    = wd["seeding_weekday"],
            total_units        = d["total_units"],
            units_per_week     = d.get("units_per_week") or 0,
            port_per_unit      = d.get("port_per_unit") or 0,
            total_ports        = d["total_ports"],
            farm_structure     = d["farm_structure"],
            seedling_box_unit  = 176,
            is_active          = 1,
            created_at         = now,
        )
        db.add(farm)
        db.flush()

        owner = FarmOwner(
            farm_id    = farm.farm_id,
            farm_name  = d["farm_name"],
            owner_name = d["owner_name"],
            phone      = d.get("phone") or "",
            email      = d.get("email") or "",
            started_at = d["started_at"],
            created_at = now,
        )
        db.add(owner)

    print(f"  farms {len(farms_data)}건 입력")


if __name__ == "__main__":
    init()