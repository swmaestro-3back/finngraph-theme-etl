import html
import re
import time

import requests
from bs4 import BeautifulSoup

from extractors.base import BaseExtractor
from models import Company, Theme

SKIP_THEMES: set[str] = set()

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

class JudalExtractor(BaseExtractor):
    source_name = "judal"

    def extract_themes(self) -> list[Theme]:
        url = "https://www.judal.co.kr/?view=themeList"
        response = requests.get(url, headers=_HEADERS, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        theme_elements = soup.find_all("th", class_=["table-success", "text-left"])

        themes: list[Theme] = []
        for element in theme_elements:
            a_tag = element.find("a")
            if not a_tag:
                continue

            b_tag = a_tag.find("b")
            theme_name = b_tag.text.strip() if b_tag else a_tag.text.strip()

            if theme_name in SKIP_THEMES:
                continue

            theme_id = None
            match = re.search(r"themeIdx=(\d+)", str(a_tag.get("href", "")))
            if match:
                theme_id = int(match.group(1))

            description = "설명 없음"
            button_tag = element.find("button")
            if button_tag:
                raw_desc = str(
                    button_tag.get("title")
                    or button_tag.get("data-bs-title")
                    or button_tag.get("data-bs-original-title")
                    or ""
                )
                if raw_desc:
                    unescaped = html.unescape(raw_desc)
                    clean_soup = BeautifulSoup(unescaped, "lxml")
                    description = re.sub(r"\s+", " ", clean_soup.get_text(separator=" ").strip())

            themes.append(Theme(name=theme_name, source="judal", theme_id=theme_id, description=description))

        return themes

    def extract_theme_stock(self, theme_id: int | None) -> list[Company]:
        url = f"https://www.judal.co.kr/?view=stockList&themeIdx={theme_id}"
        companies: list[Company] = []

        try:
            response = requests.get(url, headers=_HEADERS, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")
            th_targets = soup.find_all("th", class_="table-success text-left")

            print(f"[themeIdx={theme_id}] {len(th_targets)}개 종목 처리 중...")

            for th in th_targets:
                b_tag = th.find("b")
                company_name = b_tag.get_text(strip=True) if b_tag else ""

                span_tag = th.find("span")
                stock_info = span_tag.get_text(strip=True) if span_tag else ""

                market = ""
                srtn = None
                for part in stock_info.split():
                    if part in ("KOSPI", "KOSDAQ"):
                        market = part
                    elif part.isdigit():
                        srtn = part

                if srtn is None or market not in ("KOSPI", "KOSDAQ"):
                    continue

                button_tag = th.find("button")
                reason: str | None = None
                if button_tag:
                    raw_reason = (
                        button_tag.get("title")
                        or button_tag.get("data-bs-title")
                        or button_tag.get("data-bs-original-title")
                    )
                    reason = str(raw_reason) if raw_reason is not None else None

                companies.append(Company(name=company_name, market=market, srtn=srtn, reason=reason))

        except Exception as e:
            print(f"❌ themeIdx={theme_id} 처리 중 에러 발생: {e}")

        return companies

    def extract(self) -> list[Theme]:
        themes: list[Theme] = self.extract_themes()

        for theme in themes[:10]:
            theme.companies = self.extract_theme_stock(theme_id=theme.theme_id)
            print(f"✅ [theme_name={theme.name}] 완료")
            time.sleep(1)

        print(f"\n총 {len(themes)}개 테마 추출 완료")
        return themes
