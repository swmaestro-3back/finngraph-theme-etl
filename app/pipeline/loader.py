from core.db import neo4j_database
from models import Theme

QUERY = """
UNWIND $batch AS theme
MERGE (t:Theme {name: theme.name})
ON CREATE SET
    t.theme_id    = theme.theme_id,
    t.description = theme.description,
    t.source      = theme.source
WITH t, theme
UNWIND theme.companies AS company
MERGE (c:Company {srtn: company.srtn})
ON CREATE SET
    c.name   = company.name,
    c.market = company.market,
    c.isin   = company.isin
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
                    "name":   c.name,
                    "market": c.market,
                    "srtn":   c.srtn,
                    "reason": c.reason,
                }
                for c in theme.companies
            ],
        }
        for theme in themes
    ]

    async with neo4j_database.get_session() as session:
        await session.run(QUERY, batch=batch)

    print(f"✅ {len(themes)}개 테마 및 기업 노드, BELONGS_TO 관계 적재 완료")
