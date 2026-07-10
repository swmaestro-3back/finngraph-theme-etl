from app.crud.themes import upsert_companies, upsert_themes
from app.models import Company, Theme

async def load(themes: list[Theme], companies: list[Company]):
    company_batch = [
        {
            "name":      c.name,
            "srtnCd":    c.srtnCd,
            "market":    c.market,
            "clpr":      c.clpr,
            "vs":        c.vs,
            "fltRt":     c.fltRt,
            "trqu":      c.trqu,
            "trPrc":     c.trPrc,
            "mrktTotAmt": c.mrktTotAmt,
        }
        for c in companies
    ]

    theme_batch = [
        {
            "name":            theme.name,
            "source_theme_id": theme.source_theme_id,
            "description":     theme.description,
            "source":          theme.source,
            "companies": [
                {"srtnCd": c.srtnCd, "reason": c.reason}
                for c in theme.companies
            ],
        }
        for theme in themes
    ]

    await upsert_companies(company_batch)
    await upsert_themes(theme_batch)

    print(f"✅ {len(companies)}개 Company 노드, {len(themes)}개 Theme 및 BELONGS_TO 관계 적재 완료")
