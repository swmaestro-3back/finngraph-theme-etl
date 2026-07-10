from datetime import date, timedelta
from typing import Optional
from app.models import Company

from app.core import settings, http_client

_BASE_URL = "https://apis.data.go.kr/1160100/service/GetStockSecuritiesInfoService/getStockPriceInfo"

async def get_stock_by_opendata(stock_code: str) -> Optional[Company]:
    """공공데이터포털 API로 종목명을 조회하여 srtn 코드와 주식 정보를 반환한다.

    Args:
        stock_code: 조회할 종목 코드 (e.g. "005930")

    Returns:
        Company. 조회 결과가 없으면 None.
    """
    params = {
        "serviceKey": settings.OPENDATA_SERVICE_KEY,
        "basDt": (date.today() - timedelta(days=4)).strftime("%Y%m%d"),
        "resultType": "json",
        # "itmsNm": stock_name,
        "likeSrtnCd": stock_code
    }

    session = http_client.get_session()
    async with session.get(_BASE_URL, params=params, timeout=10) as response:
        response.raise_for_status()
        body = await response.json(content_type=None)

    items = body["response"]["body"]["items"].get("item", [])
    if not items:
        return None

    item = items[0]
    return Company(
        name=item["itmsNm"],
        srtnCd=item["srtnCd"],
        market=item["mrktCtg"],
        clpr=item["clpr"],
        vs=item["vs"],
        fltRt=item["fltRt"],
        trqu=item["trqu"],
        trPrc=item["trPrc"],
        mrktTotAmt=item["mrktTotAmt"],
    )
