import asyncio
import html
import logging
import re

from bs4 import BeautifulSoup

from app.extractors.base import BaseExtractor
from app.core import http_client
from app.models import Company, Theme

logger = logging.getLogger(__name__)

class JudalExtractor(BaseExtractor):
    source_name = "judal"
    blacklist = [
        "코스닥 퇴출기준", "지방코스닥기업", "상장폐지 위험종목", "ETF", "ETN"
    ]

    async def fetch_themes(self) -> list[Theme]:
        url = "https://www.judal.co.kr/?view=themeList"
        
        session = http_client.get_session()
        async with session.get(url, headers=self.HEADERS, timeout=self.TIMEOUT) as response:
            response.raise_for_status()
            text = await response.text()

        soup = BeautifulSoup(text, "lxml")
        theme_elements = soup.find_all("th", class_=["table-success", "text-left"])

        themes: list[Theme] = []
        for element in theme_elements:
            a_tag = element.find("a")
            if not a_tag:
                continue

            b_tag = a_tag.find("b")
            theme_name = b_tag.text.strip() if b_tag else a_tag.text.strip()
            
            # 테마 이름이 블랙리스트에 있다면 스킵
            if theme_name in self.blacklist:
                continue

            source_theme_id = None
            match = re.search(r"themeIdx=(\d+)", str(a_tag.get("href", "")))
            if match:
                source_theme_id = int(match.group(1))

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

            themes.append(Theme(name=theme_name, source="judal", source_theme_id=source_theme_id, description=description))

        return themes

    async def extract_theme_stock(self, source_theme_id: int | None) -> list[Company]:
        url = f"https://www.judal.co.kr/?view=stockList&themeIdx={source_theme_id}"
        companies: list[Company] = []

        try:
            session = http_client.get_session()
            async with session.get(url, headers=self.HEADERS, timeout=self.TIMEOUT) as response:
                response.raise_for_status()
                text = await response.text()

            soup = BeautifulSoup(text, "lxml")
            th_targets = soup.find_all("th", class_="table-success text-left")

            logger.debug(f"[themeIdx={source_theme_id}] {len(th_targets)}개 종목 처리 중...")

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

                if not srtn or market not in ("KOSPI", "KOSDAQ"):
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

                companies.append(
                    Company(
                        name=company_name,
                        ticker=srtn,
                        reason=reason
                    )
                )

        except Exception:
            logger.exception(f"themeIdx={source_theme_id} 처리 중 에러 발생")

        return companies

    async def extract(self) -> list[Theme]:
        themes: list[Theme] = await self.fetch_themes()

        for theme in themes:
            theme.companies = await self.extract_theme_stock(source_theme_id=theme.source_theme_id)
            logger.debug(f"[theme_name={theme.name}] 완료")
            await asyncio.sleep(1)

        logger.info(f"총 {len(themes)}개 테마 추출 완료")
        return themes
