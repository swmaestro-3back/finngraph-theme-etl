import re
import time

import requests
from bs4 import BeautifulSoup

from extractors.base import BaseExtractor
from models import CompanyBase, Theme

class NaverExtractor(BaseExtractor):
    """
    네이버 증권은 UTF-8이 아닌 2000년대 초반 EUC-KO로 인코딩하여 보내줌
    따라서 받은 Response를 현대적인 UTF-8로 인코딩을 하면 안되고 EUC-KO로 디코딩을 해야함
    """
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
            if pagenum == 2:
                break
            url = f"{self.BASE_URL}/sise/theme.naver?&page={pagenum}"

            # EUC-KR로 인코딩해서 보내주므로 EUC-KR로 디코딩해야함
            resp = requests.get(url, headers=self.HEADERS)
            resp.encoding = "euc-kr"

            soup = BeautifulSoup(resp.text, "lxml")
            for a in soup.select("#contentarea_left > table.type_1.theme > tr > td.col_type1 > a"):
                theme_name = a.text.strip()
                href = str(a["href"])
                theme_id = None
                match = re.search(r"no=(\d+)", href)
                if match:
                    theme_id = int(match.group(1))

                description = ""
                try:
                    detail_resp = requests.get(f"{self.BASE_URL}{href}", headers=self.HEADERS)
                    detail_resp.encoding = "euc-kr"
                    detail_soup = BeautifulSoup(detail_resp.text, "lxml")
                    info_tag = detail_soup.select_one("div.info_layer_wrap > p.info_txt")
                    if info_tag:
                        description = info_tag.text.strip()
                except Exception:
                    pass

                themes.append(Theme(name=theme_name, source="naver", theme_id=theme_id, description=description))
                print(f"✅ [{theme_name}] 테마 추출 완료")
                time.sleep(0.5)
        return themes

    def extract_theme_stock(self, theme_id: int | None = None, theme_name: str | None = None) -> list[CompanyBase]:
        url = f"{self.BASE_URL}/sise/sise_group_detail.naver?type=theme&no={theme_id}"
        companies: list[CompanyBase] = []
        try:
            resp = requests.get(url, headers=self.HEADERS)
            resp.encoding = "euc-kr"
            soup = BeautifulSoup(resp.text, "lxml")
            # 전체 테이블의 tr 파싱
            for tr in soup.select("#contentarea > div:nth-child(5) > table > tbody > tr"):
                # 주식명과 종목코드 파싱
                a = tr.select_one("td.name > div > a")
                if not a:
                    continue
                href = str(a.get("href", ""))
                if "code=" not in href:
                    continue

                name = a.text.strip()
                srtn = href.split("code=")[-1].strip()

                # 테마 편입 이유 파싱
                reason_tag = tr.select_one("div.info_layer_wrap > p.info_txt")
                reason = reason_tag.text.strip() if reason_tag else None

                companies.append(CompanyBase(name=name, srtnCd=srtn, reason=reason))

            print(f"✅ [{theme_name}] {len(companies)}개 종목 완료")

        except Exception as e:
            print(f"❌ themeCode={theme_id}, theme={theme_name} 처리 중 에러 발생: {e}")

        return companies

    def extract(self) -> list[Theme]:
        themes: list[Theme] = self.extract_themes()

        for theme in themes[:5]:
            theme.companies = self.extract_theme_stock(theme_id=theme.theme_id, theme_name=theme.name)
            time.sleep(1)

        print(f"\n총 {len(themes)}개 테마 추출 완료")
        return themes
