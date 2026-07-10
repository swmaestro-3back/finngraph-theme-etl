import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from app.extractors.factory import ExtractorFactory
from app.validator import validate
from app.transformer import transform
from app.loader import load
from app.core import neo4j_database, http_client
from app.models import Theme
from app.core import settings

SOURCES = ["judal", "naver", "antwinner"]

DATA_ROOT = Path(__file__).parent.parent / "data"

async def run_etl_pipeline(source_name: str) -> None:
    print(f"\n{'=' * 10} [{source_name}] 파이프라인 시작 {'=' * 10}")

    extractor = ExtractorFactory.get_extractor(source_name)

    themes = await extractor.extract()
    extractor.save(themes)

    validated_themes = await validate(themes)

    company_bases = [c for theme in validated_themes for c in theme.companies]
    companies = await transform(company_bases)

    await load(validated_themes, companies)

    print(f"✅ [{source_name}] 파이프라인 완료")


async def run_etl_pipeline_from_validator(source_name: str, data_folder: str) -> None:
    """extractor 단계를 건너뛰고, data/{data_folder}/{source_name}.json을 읽어 validator부터 진행한다."""
    print(f"\n{'=' * 10} [{source_name}] 파이프라인 시작 (validator부터, {data_folder}) {'=' * 10}")

    file_path = DATA_ROOT / data_folder / f"{source_name}.json"
    raw_themes = json.loads(file_path.read_text(encoding="utf-8"))
    themes = [Theme.model_validate(t) for t in raw_themes]

    validated_themes = await validate(themes)

    company_bases = [c for theme in validated_themes for c in theme.companies]
    companies = await transform(company_bases)

    await load(validated_themes, companies)

    print(f"✅ [{source_name}] 파이프라인 완료")


async def run_etl_pipeline_from_data_folder(data_folder: str) -> None:
    """data/{data_folder} 안에 있는 모든 소스 json 파일을 SOURCES 순서대로 대상으로 validator부터 진행한다."""
    folder = DATA_ROOT / data_folder
    available = {p.stem for p in folder.glob("*.json")}
    source_names = [source_name for source_name in SOURCES if source_name in available]

    for source_name in source_names:
        try:
            await run_etl_pipeline_from_validator(source_name, data_folder)
        except Exception as e:
            print(f"❌ [{source_name}] 파이프라인 실패: {e}")


async def main() -> None:
    http_client.start()
    neo4j_database.init_driver()

    try:
        # for source_name in SOURCES:
        #     try:
        #         await run_etl_pipeline(source_name)
        #     except Exception as e:
        #         print(f"❌ [{source_name}] 파이프라인 실패: {e}")

        # 테스트용: 위 for문 대신 아래 줄의 주석을 해제하면
        # data/{data_folder}에 저장된 데이터로 validator부터 진행한다.
        await run_etl_pipeline_from_data_folder("20260710")
    finally:
        await http_client.stop()
        await neo4j_database.close()


if __name__ == "__main__":
    asyncio.run(main())
