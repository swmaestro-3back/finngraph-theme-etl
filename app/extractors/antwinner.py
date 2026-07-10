from app.extractors.base import BaseExtractor
from app.models import CompanyBase, Theme
from app.core import http_client
import asyncio

_THEME_KEYWORDS_URL = "https://antwinner.com/api/proxy/theme-keywords"
_SCREENER_URL = "https://antwinner.com/api/screener"

_HEADERS = {"User-Agent": "Mozilla/5.0"}

class AntWinnerExtractor(BaseExtractor):
    source_name : str = "antwinner"

    async def extract_themes(self) -> list[Theme]:
        session = http_client.get_session()
        async with session.get(_THEME_KEYWORDS_URL, headers=_HEADERS, timeout=10) as response:
            response.raise_for_status()
            names = await response.json()
        return [Theme(name=name, source="antwinner") for name in names]

    async def extract_theme_stock(self, theme_name: str) -> list[CompanyBase]:
        params = {
            "period": "this-week",
            "rateFilter": "all",
            "sortBy": "rate",
            "themes": theme_name,
        }
        companies: list[CompanyBase] = []

        try:
            session = http_client.get_session()
            async with session.get(_SCREENER_URL, params=params, headers=_HEADERS, timeout=10) as response:
                response.raise_for_status()
                data = await response.json()

            for stock in data.get("stocks", []):
                stock_name = stock["stock_name"]
                stock_code = stock["stock_code"]

                # 가스 테마로 검색했을때 가스 라는 키워드가 포함된 모든 테마에 대한 주식이 다 나옴
                # 석유가스, 천연가스 등등 따라서 걸러줘야함
                if theme_name not in stock.get("themes", []):
                    continue
                if stock_code is None:
                    continue

                companies.append(
                    CompanyBase(
                        name=stock_name,
                        srtnCd=stock_code,
                        reason=None
                    )
                )

            print(f"✅ [{theme_name}] {len(companies)}개 종목 완료")

        except Exception as e:
            print(f"❌ theme={theme_name} 처리 중 에러 발생: {e}")

        return companies

    async def extract(self) -> list[Theme]:
        themes: list[Theme] = await self.extract_themes()
        for theme in themes:
            theme.companies = await self.extract_theme_stock(theme.name)
            # 429 Client Error Rate Limiting 방지
            await asyncio.sleep(2)

        print(f"\n총 {len(themes)}개 테마 추출 완료")
        return themes
