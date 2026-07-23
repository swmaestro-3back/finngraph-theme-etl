import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from app.extractors.judal import JudalExtractor
from app.core import http_client, setup_logging


async def main():
    setup_logging()
    http_client.start()
    try:
        extractor = JudalExtractor()
        await extractor.run()
    finally:
        await http_client.stop()


if __name__ == "__main__":
    asyncio.run(main())