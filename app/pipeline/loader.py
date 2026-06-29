from core.db import neo4j_database
from models import Company, Theme

QUERY = """
UNWIND $batch AS theme
MERGE (t:Theme {name: theme.name})
ON CREATE SET
    t.theme_id    = theme.theme_id,
    t.description = theme.description,
    t.source      = theme.source
WITH t, theme
UNWIND theme.companies AS company
MERGE (c:Company {srtnCd: company.srtnCd})
SET
    c.name       = company.name,
    c.market     = company.market,
    c.clpr       = company.clpr,
    c.vs         = company.vs,
    c.fltRt      = company.fltRt,
    c.trqu       = company.trqu,
    c.trPrc      = company.trPrc,
    c.mrkTotAmt  = company.mrkTotAmt
MERGE (c)-[r:BELONGS_TO]->(t)
ON CREATE SET r.reason = company.reason
"""

async def load(themes: list[Theme]):
    batch = [
        {
            "name":        theme.name,
            "theme_id":    theme.theme_id,
            "description": theme.description,
            "source":      theme.source,
            "companies": [
                {
                    "name":      c.name,
                    "srtnCd":    c.srtnCd,
                    "reason":    c.reason,
                    "market":    c.market,
                    "clpr":      c.clpr,
                    "vs":        c.vs,
                    "fltRt":     c.fltRt,
                    "trqu":      c.trqu,
                    "trPrc":     c.trPrc,
                    "mrkTotAmt": c.mrkTotAmt,
                }
                for c in theme.companies
                if isinstance(c, Company)
            ],
        }
        for theme in themes
    ]

    async with neo4j_database.get_session() as session:
        await session.run(QUERY, batch=batch)

    print(f"✅ {len(themes)}개 테마 및 기업 노드, BELONGS_TO 관계 적재 완료")
