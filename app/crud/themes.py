from app.core import neo4j_database

async def theme_exists() -> bool:
    records = await neo4j_database.execute(
        """
MATCH (t:Theme)
RETURN t LIMIT 1
"""
    )
    return len(records) > 0

async def fetch_theme_stock_map() -> dict[str, set[str]]:
    records = await neo4j_database.execute(
        """
MATCH (t:Theme)
OPTIONAL MATCH (c:Company)-[:BELONGS_TO]->(t)
RETURN t.name AS theme_name, coalesce(t.description, '') AS description, collect(c.srtnCd) AS srtn_codes
"""
    )
    return {r["theme_name"]: set(r["srtn_codes"]) for r in records}

async def fetch_existing_company_srtn_codes() -> set[str]:
    records = await neo4j_database.execute(
        """
MATCH (c:Company)
RETURN c.srtnCd AS srtnCd
"""
    )
    return {r["srtnCd"] for r in records}

async def fetch_company_srtn_by_names(names: list[str]) -> dict[str, str]:
    """name으로 기존 Neo4j Company를 조회해 name -> srtnCd 매핑을 반환한다."""
    records = await neo4j_database.execute(
        """
UNWIND $names AS name
MATCH (c:Company {name: name})
RETURN c.name AS name, c.srtnCd AS srtnCd
""",
        parameters={"names": names},
    )
    return {r["name"]: r["srtnCd"] for r in records}

async def upsert_companies(company_batch: list[dict]) -> None:
    await neo4j_database.execute(
        """
UNWIND $companies AS company
MERGE (c:Company {srtnCd: company.srtnCd})
SET
    c.name       = company.name,
    c.market     = company.market,
    c.clpr       = company.clpr,
    c.vs         = company.vs,
    c.fltRt      = company.fltRt,
    c.trqu       = company.trqu,
    c.trPrc      = company.trPrc,
    c.mrktTotAmt  = company.mrktTotAmt
""",
    parameters={"companies": company_batch},
    )

async def upsert_themes(theme_batch: list[dict]) -> None:
    await neo4j_database.execute(
        """
UNWIND $batch AS theme
MERGE (t:Theme {name: theme.name})
ON CREATE SET
    t.id = randomUUID(),
    t.source_theme_id = theme.source_theme_id,
    t.description = theme.description,
    t.source = theme.source
WITH t, theme
UNWIND theme.companies AS company
MATCH (c:Company {srtnCd: company.srtnCd})
MERGE (c)-[r:BELONGS_TO]->(t)
ON CREATE SET r.reason = company.reason
""",
    parameters={"batch": theme_batch},
    )
