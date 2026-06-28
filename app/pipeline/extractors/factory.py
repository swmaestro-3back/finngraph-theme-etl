from extractors.naver import NaverExtractor
from extractors.judal import JudalExtractor
from extractors.antwinner import AntWinnerExtractor
from extractors.base import BaseExtractor

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
            return ValueError("Not Available Source Name")