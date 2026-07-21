import asyncio
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from app.extractors.factory import ExtractorFactory
from app.validator import validate
from app.loader import load
from app.core import neo4j_database, http_client, setup_logging
from app.models import Theme
from app.core import settings

logger = logging.getLogger(__name__)

SOURCES = ["judal", "naver", "antwinner"]

DATA_ROOT = Path(__file__).parent.parent / "data"

async def run_etl_pipeline() -> None:
    """모든 SOURCE를 순차로 extract한 뒤, 모아진 데이터를 대상으로
    validate/load를 한 번씩만 수행한다."""
    all_themes: list[Theme] = []

    for source_name in SOURCES:
        logger.info(f"[{source_name}] 추출 시작")
        extractor = ExtractorFactory.get_extractor(source_name)
        themes = await extractor.extract()
        extractor.save(themes)
        all_themes.extend(themes)

    validated_themes = await validate(all_themes)
    await load(validated_themes)

    logger.info("전체 파이프라인 완료")


def _load_themes_from_file(source_name: str, data_folder: str) -> list[Theme]:
    file_path = DATA_ROOT / data_folder / f"{source_name}.json"
    raw_themes = json.loads(file_path.read_text(encoding="utf-8"))
    return [Theme.model_validate(t) for t in raw_themes]


async def run_etl_pipeline_from_data_folder(data_folder: str) -> None:
    """extractor 단계를 건너뛰고, data/{data_folder} 안의 모든 소스 json을 읽어
    모아진 데이터를 대상으로 validate/load를 한 번씩만 수행한다."""
    logger.info(f"파이프라인 시작 (data부터, {data_folder})")

    folder = DATA_ROOT / data_folder
    available = {p.stem for p in folder.glob("*.json")}
    source_names = [source_name for source_name in SOURCES if source_name in available]

    all_themes: list[Theme] = []
    for source_name in source_names:
        all_themes.extend(_load_themes_from_file(source_name, data_folder))

    validated_themes = await validate(all_themes)
    await load(validated_themes)

    logger.info("전체 파이프라인 완료")


async def main() -> None:
    http_client.start()
    logger.info("HTTP Client 시작")
    neo4j_database.init_driver()
    logger.info("Neo4j Driver 초기화 완료")

    try:
        await run_etl_pipeline()

        # 테스트용: 위 줄 대신 아래 줄의 주석을 해제하면
        # data/{data_folder}에 저장된 데이터로 validate부터 진행한다.
        # await run_etl_pipeline_from_data_folder("20260710")
    finally:
        await http_client.stop()
        await neo4j_database.close()
        logger.info("HTTP Client 및 Neo4j Driver 종료")


if __name__ == "__main__":
    setup_logging()
    asyncio.run(main())
