from app.extractors.naver import NaverExtractor
from app.extractors.judal import JudalExtractor
from app.extractors.antwinner import AntWinnerExtractor
from app.extractors.base import BaseExtractor

class ExtractorFactory:
    @staticmethod
    def get_extractor(source_name: str) -> BaseExtractor:
        if source_name == "naver":
            return NaverExtractor()
        elif source_name == "judal":
            return JudalExtractor()
        elif source_name == "antwinner":
            return AntWinnerExtractor()
        else:
            raise ValueError("Not Available Source Name")