"""
Theme 크롤링하면서 얻은 CompanyBase 정보를 바탕으로 Company 정보로 변환하여 반환

1. 중복 제거된 고유한 종목코드(srtnCd) 리스트 확보
2. get_stock_by_krx를 통해 각 종목에 대한 Company 정보 조회
"""

import asyncio
import json
from pathlib import Path

from app.models import Company, CompanyBase
from app.utils.opendata import get_stock_by_opendata
from app.crud.themes import fetch_existing_company_srtn_codes

# 공공데이터포털 API 초당 최대 트랜잭션(30 TPS) 제한을 피하기 위한 배치 크기/간격
# 배치 내 요청은 거의 동시에 나가므로, 배치 크기가 TPS 한도(30)를 넘으면 안 된다.
_BATCH_SIZE = 10
_BATCH_INTERVAL_SECONDS = 1

_DATA_ROOT = Path(__file__).parents[1] / "data"


def _save_partial(companies: list[Company | None]) -> None:
    """에러로 중단됐을 때, 그때까지 조회에 성공한 Company를 백업 저장한다."""
    valid = [c for c in companies if c is not None]
    output = _DATA_ROOT / "company.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps([c.model_dump() for c in valid], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"⚠️ transform 중 에러 발생, 지금까지 조회한 {len(valid)}개 Company를 {output}에 저장했습니다.")


async def transform(company_bases: list[CompanyBase]) -> list[Company]:
    # 종목코드 중복제거
    candidate_srtn_codes = {cb.srtnCd for cb in company_bases}

    # Neo4j에 이미 있는 종목은 재조회하지 않고 건너뜀
    existing_srtn_codes = await fetch_existing_company_srtn_codes()
    unique_srtn_codes = list(candidate_srtn_codes - existing_srtn_codes)

    skipped = len(candidate_srtn_codes) - len(unique_srtn_codes)
    if skipped:
        print(f"[transform] 이미 Neo4j에 있는 {skipped}개 종목은 건너뜁니다.")

    # 20개씩 묶어서 1초 간격으로 호출
    total = len(unique_srtn_codes)
    companies: list[Company | None] = []

    for i in range(0, total, _BATCH_SIZE):
        batch = unique_srtn_codes[i:i + _BATCH_SIZE]
        end = min(i + _BATCH_SIZE, total)
        print(f"[transform] {total}개 중 {i + 1}~{end}번째 조회 중...")

        tasks = [get_stock_by_opendata(srtn_code) for srtn_code in batch]
        try:
            companies.extend(await asyncio.gather(*tasks))
        except Exception:
            _save_partial(companies)
            raise

        if end < total:
            await asyncio.sleep(_BATCH_INTERVAL_SECONDS)

    # None인 것은 제외하여 반환
    return [company for company in companies if company is not None]
