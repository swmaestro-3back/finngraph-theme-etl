import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
sys.path.insert(0, str(Path(__file__).parents[1] / "app"))
sys.path.insert(0, str(Path(__file__).parents[1] / "app" / "pipeline"))

from app.extractors.judal import JudalExtractor
from app.core import http_client


async def main():
    http_client.start()
    try:
        extractor = JudalExtractor()
        await extractor.run()
    finally:
        await http_client.stop()


if __name__ == "__main__":
    asyncio.run(main())