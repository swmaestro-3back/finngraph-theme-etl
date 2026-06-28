import time

import requests

from extractors.base import BaseExtractor
from models import Company, Theme
from utils.krx import get_stock_by_krx

_THEME_KEYWORDS_URL = "https://antwinner.com/api/proxy/theme-keywords"
_SCREENER_URL = "https://antwinner.com/api/screener"

_HEADERS = {"User-Agent": "Mozilla/5.0"}


class AntWinnerExtractor(BaseExtractor):
    source_name = "antwinner"

    def extract_themes(self) -> list[Theme]:
        response = requests.get(_THEME_KEYWORDS_URL, headers=_HEADERS, timeout=10)
        response.raise_for_status()
        return [Theme(name=name, source="AntWinner") for name in response.json()]

    def extract_theme_stock(self, theme_name: str) -> list[Company]:
        params = {
            "period": "this-week",
            "rateFilter": "all",
            "sortBy": "rate",
            "themes": theme_name,
        }
        companies: list[Company] = []

        try:
            response = requests.get(_SCREENER_URL, params=params, headers=_HEADERS, timeout=10)
            response.raise_for_status()
            data = response.json()

            for s in data.get("stocks", []):
                srtn = s.get("stock_code", "")
                # 가스 테마로 검색했을때 가스 라는 키워드가 포함된 모든 테마에 대한 주식이 다 나옴
                # 석유가스, 천연가스 등등 따라서 걸러줘야함
                if theme_name not in s.get("themes", []):
                    continue

                if len(srtn) < 6:
                    # stock_code가 없으면 KRX API로 종목명 조회해서 srtn, market 보완
                    krx_stock = get_stock_by_krx(s["stock_name"])
                    if krx_stock is None:
                        continue
                    srtn = krx_stock.srtn
                    market = krx_stock.market
                else:
                    market = None
                companies.append(Company(name=s["stock_name"], srtn=srtn, market=market, reason=None))

            print(f"✅ [{theme_name}] {len(companies)}개 종목 완료")

        except Exception as e:
            print(f"❌ theme={theme_name} 처리 중 에러 발생: {e}")

        return companies

    def extract(self) -> list[Theme]:
        themes: list[Theme] = self.extract_themes()
        for theme in themes:
            theme.companies = self.extract_theme_stock(theme.name)
            # 429 Client Error Rate Limiting 방지
            time.sleep(2)

        print(f"\n총 {len(themes)}개 테마 추출 완료")
        return themes
