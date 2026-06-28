from abc import ABC, abstractmethod
from pathlib import Path
from datetime import date
import json
from models import Theme, Company

_DATA_ROOT = Path(__file__).parents[3] / "data"

class BaseExtractor(ABC):

    source_name: str

    @abstractmethod
    def extract_themes(self) -> list[Theme]:
        """소스에서 테마 목록만 추출한다 (종목 정보 미포함).

        companies 필드가 빈 상태의 경량 Theme 객체를 반환하며,
        전체 파이프라인의 첫 번째 단계로 사용된다.

        Returns:
            companies가 빈 list[Theme]. theme_id가 없는 소스는 None으로 설정된다.
        """
        pass

    @abstractmethod
    def extract_theme_stock(self, theme_id: int | None = None, theme_name: str | None = None) -> list[Company]:
        """특정 테마에 속한 종목 목록을 추출한다.

        Args:
            theme_id: 소스에서 사용하는 테마 고유 ID. ID 기반 조회를 지원하지 않는
                소스(e.g. AntWinner)는 None으로 전달한다.
            theme_name: 테마명. ID가 없는 소스에서 조회 키로 사용되며,
                로깅 및 디버깅 목적으로도 활용된다.

        Returns:
            해당 테마에 속한 list[Company]. 조회 실패 시 빈 리스트를 반환한다.
        """
        pass

    @abstractmethod
    def extract(self) -> list[Theme]:
        """테마 목록과 각 테마의 종목을 모두 수집하여 완성된 데이터를 반환한다.

        extract_themes로 테마 목록을 가져온 뒤, 각 테마에 대해
        extract_theme_stock을 호출하여 companies를 채운다.

        Returns:
            companies가 채워진 list[Theme].
        """
        pass

    def save(self, themes: list[Theme]) -> Path:
        """수집된 테마 데이터를 JSON 파일로 저장한다.

        저장 경로: {project_root}/data/{오늘날짜}/{source_name}.json

        Args:
            themes: 저장할 list[Theme]. extract()의 반환값을 그대로 전달한다.

        Returns:
            저장된 파일의 절대 경로(Path).
        """
        folder = _DATA_ROOT / date.today().strftime("%Y%m%d")
        folder.mkdir(parents=True, exist_ok=True)
        output = folder / f"{self.source_name}.json"
        output.write_text(
            json.dumps([t.model_dump() for t in themes], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return output

    def run(self) -> Path:
        """파이프라인 진입점. 수집 후 저장까지 순서를 보장한다.

        Returns:
            저장된 파일의 절대 경로(Path).
        """
        themes = self.extract()
        return self.save(themes)
