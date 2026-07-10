import math
from core.db import neo4j_database
from core.embedding import embedding_model
from models import Company, Theme

JACCARD_THRESHOLD = 0.7
EMBEDDING_THRESHOLD = 0.90
MIN_STOCKS_FOR_JACCARD = 5

FETCH_QUERY = """
MATCH (t:Theme)
OPTIONAL MATCH (c:Company)-[:BELONGS_TO]->(t)
RETURN t.name AS theme_name, coalesce(t.description, '') AS description, collect(c.srtnCd) AS srtn_codes
"""

def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return dot / norm if norm > 0 else 0.0


def _is_jaccard_similar(candidate: set[str], stock_sets: dict[str, set[str]]) -> bool:
    if len(candidate) < MIN_STOCKS_FOR_JACCARD:
        return False
    return any(_jaccard(candidate, s) >= JACCARD_THRESHOLD for s in stock_sets.values())


def _is_embedding_similar(candidate_emb: list[float], embeddings: dict[str, list[float]]) -> bool:
    return any(_cosine(candidate_emb, e) >= EMBEDDING_THRESHOLD for e in embeddings.values())


async def validate(themes: list[Theme]) -> list[Theme]:
    """
    transform과 load 사이에서 사용
    """
    async with neo4j_database.get_session() as session:
        result = await session.run(FETCH_QUERY)
        records = await result.data()

    existing_sets: dict[str, set[str]] = {
        r["theme_name"]: set(r["srtn_codes"]) for r in records
    }

    existing_embeddings: dict[str, list[float]] = {}
    if records:
        existing_texts = [f"{r['theme_name']} {r['description']}".strip() for r in records]
        embs = embedding_model.get_embeddings(existing_texts)
        existing_embeddings = {r["theme_name"]: emb for r, emb in zip(records, embs)}

    new_embeddings: list[list[float]] = []
    if themes:
        new_texts = [f"{t.name} {t.description}".strip() for t in themes]
        new_embeddings = embedding_model.get_embeddings(new_texts)

    accepted: list[Theme] = []
    accepted_sets: dict[str, set[str]] = {}
    accepted_embeddings: dict[str, list[float]] = {}

    for theme, theme_emb in zip(themes, new_embeddings):
        # 1. Exact name match fast-path (Neo4j)
        if theme.name in existing_sets:
            print(f"⛔ [{theme.name}] Neo4j에 동일 이름 존재, 제거")
            continue

        candidate_set = {c.srtnCd for c in theme.companies if isinstance(c, Company)}

        # 2. Jaccard check against Neo4j (skip for small themes)
        if _is_jaccard_similar(candidate_set, existing_sets):
            print(f"⛔ [{theme.name}] Neo4j 기존 테마와 종목 유사 (Jaccard >= {JACCARD_THRESHOLD}), 제거")
            continue

        # 3. Embedding check against Neo4j
        if _is_embedding_similar(theme_emb, existing_embeddings):
            print(f"⛔ [{theme.name}] Neo4j 기존 테마와 의미 유사 (cosine >= {EMBEDDING_THRESHOLD}), 제거")
            continue

        # 4. Exact name match fast-path (batch)
        if theme.name in accepted_sets:
            print(f"⛔ [{theme.name}] 배치 내 동일 이름 존재, 제거")
            continue

        # 5. Jaccard check against accepted batch themes
        if _is_jaccard_similar(candidate_set, accepted_sets):
            print(f"⛔ [{theme.name}] 배치 내 테마와 종목 유사 (Jaccard >= {JACCARD_THRESHOLD}), 제거")
            continue

        # 6. Embedding check against accepted batch themes
        if _is_embedding_similar(theme_emb, accepted_embeddings):
            print(f"⛔ [{theme.name}] 배치 내 테마와 의미 유사 (cosine >= {EMBEDDING_THRESHOLD}), 제거")
            continue

        accepted.append(theme)
        accepted_sets[theme.name] = candidate_set
        accepted_embeddings[theme.name] = theme_emb

    print(f"✅ {len(accepted)}/{len(themes)}개 테마 유효성 검사 통과")
    return accepted
