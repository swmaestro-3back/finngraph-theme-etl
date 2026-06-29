import os

import requests
from datetime import date
from dotenv import load_dotenv
from typing import Literal
from pydantic import BaseModel, Field

load_dotenv()

_BASE_URL = "https://apis.data.go.kr/1160100/service/GetStockSecuritiesInfoService/getStockPriceInfo"


class KRXStock(BaseModel):
    name: str = Field(..., description="주식 종목명", examples=["삼성전자"])
    srtnCd: str = Field(..., min_length=6, max_length=7, description="KRX 거래소 단축 코드")
    market: Literal["KOSPI", "KOSDAQ"] = Field(..., description="거래소 구분")
    clpr: int = Field(..., description="종가")
    vs: int = Field(..., description="전일대비 등락")
    fltRt: float = Field(..., description="등락률")
    trqu: int = Field(..., description="거래량")
    trPrc: int = Field(..., description="거래대금")
    mrkTotAmt: int = Field(..., description="시가총액")


def get_stock_price(srtn_cd: str) -> dict | None:
    """srtnCd로 KRX API를 조회하여 시세 정보를 반환한다.

    Returns:
        API 응답 item dict. 조회 결과 없으면 None.
    """
    params = {
        "serviceKey": os.getenv("KRX_SERVICE_KEY"),
        "basDt": date.today().strftime("%Y%m%d"),
        "resultType": "json",
        "srtnCd": srtn_cd,
    }
    response = requests.get(_BASE_URL, params=params, timeout=10)
    response.raise_for_status()

    items = response.json()["response"]["body"]["items"].get("item", [])
    return items[0] if items else None


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
        srtnCd=item["srtnCd"],
        market=item["mrktCtg"],
        clpr=item["clpr"],
        vs=item["vs"],
        fltRt=item["fltRt"],
        trqu=item["trqu"],
        trPrc=item["trPrc"],
        mrkTotAmt=item["mrkTotAmt"],
    )
