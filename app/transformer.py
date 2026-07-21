"""
Theme 크롤링으로 얻은 Company(name, srtnCd)를 Neo4j에 이미 저장된 Company와 대조하여 검증한다.

1. 테마 전체의 종목명을 모아 Neo4j Company를 name으로 일괄 조회한다.
2. name이 Neo4j에 없으면 해당 종목을 제외한다.
3. name은 있으나 크롤링한 srtnCd와 Neo4j의 srtnCd가 다르면 해당 종목을 제외한다.
"""

from app.models import Theme
from app.crud.themes import fetch_company_srtn_by_names


async def transform(themes: list[Theme]) -> list[Theme]:
    names = {c.name for theme in themes for c in theme.companies}
    name_to_srtn = await fetch_company_srtn_by_names(list(names))

    for theme in themes:
        resolved = []
        for c in theme.companies:
            srtn = name_to_srtn.get(c.name)
            if srtn is None:
                print(f"⚠️ [{theme.name}] '{c.name}' Neo4j에 존재하지 않아 제외합니다.")
                continue
            if c.srtnCd != srtn:
                print(f"⚠️ [{theme.name}] '{c.name}' srtnCd 불일치 (크롤링={c.srtnCd}, Neo4j={srtn}) 제외합니다.")
                continue
            resolved.append(c)
        theme.companies = resolved

    return themes
