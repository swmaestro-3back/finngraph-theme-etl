import os

import requests
from datetime import date
from dotenv import load_dotenv
from typing import Literal
from pydantic import BaseModel

load_dotenv()

_BASE_URL = "https://apis.data.go.kr/1160100/service/GetStockSecuritiesInfoService/getStockPriceInfo"


class KRXStock(BaseModel):
    name: str
    srtn: str
    market: Literal["KOSPI", "KOSDAQ"]


def get_stock_by_krx(stock_name: str) -> KRXStock | None:
    """KRX 공공 API로 종목명을 조회하여 srtn 코드와 시장 정보를 반환한다.

    Args:
        stock_name: 조회할 종목명 (e.g. "문배철강")

    Returns:
        KRXStock. 조회 결과가 없으면 None.
    """
    params = {
        "serviceKey": os.getenv("KRX_SERVICE_KEY"),
        "basDt": date.today().strftime("%Y%m%d"),
        "resultType": "json",
        "itmsNm": stock_name,
    }
    response = requests.get(_BASE_URL, params=params, timeout=10)
    response.raise_for_status()

    items = response.json()["response"]["body"]["items"].get("item", [])
    if not items:
        return None

    item = items[0]
    return KRXStock(
        name=item["itmsNm"],
        srtn=item["srtnCd"],
        market=item["mrktCtg"],
    )
