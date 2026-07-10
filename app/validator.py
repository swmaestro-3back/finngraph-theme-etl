import re

from app.crud.themes import fetch_theme_stock_map, theme_exists
from app.models import CompanyBase, Theme

CONTAINMENT_OVERLAP_THRESHOLD = 0.9
MIN_STOCKS_FOR_CONTAINMENT = 5
MIN_CONTAINMENT_NAME_LENGTH = 2

def _normalize_name(name: str) -> str:
    """공백 표기 차이(예: "2차 전지" vs "2차전지")로 인한 미매칭을 막기 위해 모든 공백을 제거한다."""
    return re.sub(r"\s+", "", name)

def _overlap_coefficient(a: set[str], b: set[str]) -> float:
    """교집합 / 두 집합 중 작은 쪽 크기. 이름이 포함 관계일 때(크기 차가 큰 두 집합) 쓰는 지표."""
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


def _is_name_contained(normalized_a: str, normalized_b: str) -> bool:
    shorter, longer = sorted([normalized_a, normalized_b], key=len)
    if len(shorter) < MIN_CONTAINMENT_NAME_LENGTH:
        return False
    return shorter in longer


def _find_duplicate_name(theme: Theme, candidate_stocks: set[str], name_to_stocks: dict[str, set[str]]) -> str | None:
    """이름이 완전히 같거나, 이름이 포함 관계이면서 종목이 THRESHOLD 이상 겹치는 기존 테마명을 찾는다."""
    normalized_theme_name = _normalize_name(theme.name)

    for existing_name in name_to_stocks:
        if _normalize_name(existing_name) == normalized_theme_name:
            return existing_name

    if len(candidate_stocks) < MIN_STOCKS_FOR_CONTAINMENT:
        return None

    for existing_name, existing_stocks in name_to_stocks.items():
        if len(existing_stocks) < MIN_STOCKS_FOR_CONTAINMENT:
            continue
        if not _is_name_contained(normalized_theme_name, _normalize_name(existing_name)):
            continue
        if _overlap_coefficient(candidate_stocks, existing_stocks) >= CONTAINMENT_OVERLAP_THRESHOLD:
            return existing_name

    return None


async def validate(themes: list[Theme]) -> list[Theme]:
    """
    transform과 load 사이에서 사용.

    이름이 동일하거나, 이름이 포함 관계(예: "반도체" ⊂ "반도체소재")이면서
    종목이 CONTAINMENT_OVERLAP_THRESHOLD 이상 겹치는 테마는 새 노드를 만들지 않고
    기존(Neo4j) 또는 같은 배치 내 먼저 발견된 테마로 종목을 병합한다.
    """
    existing_stocks: dict[str, set[str]] = {}
    if await theme_exists():
        existing_stocks = await fetch_theme_stock_map()

    merged: dict[str, Theme] = {}
    merged_stocks: dict[str, set[str]] = {}

    for theme in themes:
        candidate_stocks = {c.srtnCd for c in theme.companies if isinstance(c, CompanyBase)}

        dup_name = _find_duplicate_name(theme, candidate_stocks, merged_stocks)
        if dup_name is None:
            dup_name = _find_duplicate_name(theme, candidate_stocks, existing_stocks)

        if dup_name is None:
            merged[theme.name] = theme
            merged_stocks[theme.name] = candidate_stocks
            continue

        if dup_name in merged:
            target = merged[dup_name]
            target_srtn = merged_stocks[dup_name]
            for c in theme.companies:
                if isinstance(c, CompanyBase) and c.srtnCd not in target_srtn:
                    target.companies.append(c)
                    target_srtn.add(c.srtnCd)
            print(f"🔗 [{theme.name}] → [{dup_name}] 배치 내 테마로 병합 (병합 종목 {len(candidate_stocks)}개, 최종 종목 {len(target_srtn)}개)")
        else:
            # Neo4j에 이미 있는 테마와 병합: 이름을 기존 테마명으로 맞춰서
            # loader의 MERGE (t:Theme {name: ...})가 같은 노드에 종목을 붙이게 한다.
            merged_srtn = existing_stocks[dup_name] | candidate_stocks
            print(f"🔗 [{theme.name}] Neo4j 기존 테마 [{dup_name}]에 병합 (병합 종목 {len(candidate_stocks)}개, 최종 종목 {len(merged_srtn)}개)")
            theme.name = dup_name
            merged[dup_name] = theme
            merged_stocks[dup_name] = merged_srtn

    accepted = list(merged.values())
    print(f"✅ {len(themes)}개 테마 → {len(accepted)}개로 병합 완료")
    return accepted
