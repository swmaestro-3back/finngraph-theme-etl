import logging

from app.crud import upsert_themes
from app.models import Theme

logger = logging.getLogger(__name__)

async def load(themes: list[Theme]):
    theme_batch = [
        {
            "name":            theme.name,
            "source_theme_id": theme.source_theme_id,
            "description":     theme.description,
            "source":          theme.source,
            "companies": [
                {"ticker": c.ticker, "reason": c.reason}
                for c in theme.companies
            ],
        }
        for theme in themes
    ]

    await upsert_themes(theme_batch)

    logger.info(f"{len(themes)}개 Theme 및 BELONGS_TO 관계 적재 완료")
