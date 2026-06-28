import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "app"))
sys.path.insert(0, str(Path(__file__).parents[1] / "app" / "pipeline"))

from extractors.judal import JudalExtractor

if __name__ == "__main__":
    extractor = JudalExtractor()

    path = extractor.run()
    print(f"\n저장 완료: {path}")
