import re
import time

import requests
from bs4 import BeautifulSoup

from extractors.base import BaseExtractor
from models import Company, Theme


class NaverExtractor(BaseExtractor):
    source_name = "naver"
    BASE_URL = "https://finance.naver.com"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36",
        "Upgrade-Insecure-Requests": "1",
        "DNT": "1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
    }

    def extract_themes(self) -> list[Theme]:
        themes: list[Theme] = []
        for pagenum in range(1, 8):
            url = f"{self.BASE_URL}/sise/theme.nhn?field=name&ordering=asc&page={pagenum}"
            resp = requests.get(url, headers=self.HEADERS)
            soup = BeautifulSoup(resp.content, "html.parser")
            for a in soup.select("#contentarea_left > table.type_1.theme > tr > td.col_type1 > a"):
                theme_name = a.text.strip()
                href = str(a["href"])
                theme_id = None
                match = re.search(r"themeCode=(\d+)", href)
                if match:
                    theme_id = int(match.group(1))
                themes.append(Theme(name=theme_name, source="Naver", theme_id=theme_id))
        return themes

    def extract_theme_stock(self, theme_id: int | None = None, theme_name: str | None = None) -> list[Company]:
        url = f"{self.BASE_URL}/sise/themeMain.nhn?themeCode={theme_id}"
        companies: list[Company] = []
        try:
            resp = requests.get(url, headers=self.HEADERS)
            soup = BeautifulSoup(resp.content, "html.parser")
            for a in soup.select("#contentarea > div:nth-child(5) > table > tbody > tr > td.name > div > a"):
                name = a.text.strip()
                href = str(a.get("href", ""))
                if "code=" not in href:
                    continue
                srtn = href.split("code=")[-1].strip()
                companies.append(Company(name=name, srtn=srtn, market=None, reason=None))

            print(f"✅ [{theme_name}] {len(companies)}개 종목 완료")

        except Exception as e:
            print(f"❌ themeCode={theme_id}, theme={theme_name} 처리 중 에러 발생: {e}")

        return companies

    def extract(self) -> list[Theme]:
        themes: list[Theme] = self.extract_themes()

        for theme in themes:
            theme.companies = self.extract_theme_stock(theme_id=theme.theme_id, theme_name=theme.name)
            time.sleep(1)

        print(f"\n총 {len(themes)}개 테마 추출 완료")
        return themes
