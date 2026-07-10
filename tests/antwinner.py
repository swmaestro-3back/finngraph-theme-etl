import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
sys.path.insert(0, str(Path(__file__).parents[1] / "app"))
sys.path.insert(0, str(Path(__file__).parents[1] / "app" / "pipeline"))

from app.pipeline.extractors import AntWinnerExtractor

if __name__ == "__main__":
    extractor = AntWinnerExtractor()
    extractor.run()
