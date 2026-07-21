# finngraph-theme-etl

주식 테마(테마주) 데이터를 여러 소스에서 크롤링해 Neo4j GraphDB에 적재하는 ETL 파이프라인.

## 개요

`naver`, `judal`, `antwinner` 3개 소스에서 테마명과 소속 종목을 크롤링(Extract) →
Neo4j에 이미 존재하는 테마/종목과 대조해 검증 및 병합(Validate) →
Neo4j에 `Theme`, `Company` 노드와 `BELONGS_TO` 관계로 적재(Load)하는 구조.

## 디렉터리 구조

```
app/
  core/         # 환경변수 설정(configs), Neo4j 드라이버(db), HTTP 클라이언트(http), 로깅(logger)
  crud/         # Neo4j 쿼리 (themes.py)
  extractors/   # 소스별 크롤러 (base, naver, judal, antwinner, factory)
  models.py     # Theme, Company pydantic 모델
  validator.py  # 검증/병합 로직
  loader.py     # Neo4j 적재
  main.py       # 진입점
data/           # 소스별 크롤링 결과 JSON (날짜별 폴더)
logs/           # debug.log(전체), error.log(에러만)
tests/          # 소스별 추출 로직 테스트
```

## 파이프라인

```
extract (per source) -> save(JSON) -> validate(company/theme 병합) -> load(Neo4j)
```

- **Extract**: `app/extractors/{naver,judal,antwinner}.py` — 각 소스별 `BaseExtractor` 구현체.
  - `fetch_themes()`: 블랙리스트 제외한 테마명 크롤링
  - `extract_theme_stock()`: 테마별 소속 종목 크롤링
  - `extract()` 결과는 `data/{YYYYMMDD}/{source}.json`으로 저장
  - `app/extractors/factory.py`의 `ExtractorFactory.get_extractor(source_name)`으로 소스명에 맞는 Extractor를 팩토리 메서드 패턴으로 생성
- **Validate**: `app/validator.py`
  - `validate_company`: 크롤링한 종목명/ticker를 Neo4j 기존 `Company`와 대조, 불일치·미존재 종목 제외
  - `validate_theme`: 이름 동일 또는 이름 포함 관계 + 종목 overlap(임계값 0.9) 기준으로 기존/배치 내 테마와 병합
- **Load**: `app/loader.py` → `app/crud/themes.py`의 `upsert_themes`로 Neo4j에 반영

`app/main.py`가 진입점.
`run_etl_pipeline()`은 크롤링부터 전체 실행하고,
`run_etl_pipeline_from_data_folder(data_folder)`는 Data Lake 역할인 JSON 파일부터 validate → load만 재실행할 때 사용.

## 요구 사항

- Python >= 3.13
- [uv](https://docs.astral.sh/uv/) (의존성 관리)
- Neo4j 인스턴스

## 설치 및 실행

```bash
uv sync

cp .env.example .env
# .env에 NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, NEO4J_DATABASE 입력

uv run python -m app.main
```

## 환경 변수

`.env.example` 참고:

| 변수             | 설명           |
| ---------------- | -------------- |
| `NEO4J_URI`      | Neo4j 접속 URI |
| `NEO4J_USERNAME` | Neo4j 사용자명 |
| `NEO4J_PASSWORD` | Neo4j 비밀번호 |
| `NEO4J_DATABASE` | 사용할 DB 이름 |

## 로깅

`app/core/logger.py`의 `setup_logging()`이 `app/main.py` 실행 시 1회 호출됨:

- console: INFO 이상
- `logs/debug.log`: DEBUG 이상 전체
- `logs/error.log`: ERROR만

## 테스트

- 각 소스에 대한 테스트를 개별적으로 진행 가능
- 테스트 결과는 `data/{YYYYMMDD}/{source}.json` 에서 확인 가능

```bash
uv run tests/naver.py
```
